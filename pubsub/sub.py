from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import socket
from functools import wraps

import kombu

from . import get_config_param, AMQP_URL, MODEL_EXCHANGE

# List of tuples (Queue, Callback)
_topic_registry = []


def _create_or_verify_queue(amqp_url, *args, **kwargs):
    """Create or verify existence of queue on AMQP server.
    """
    queue = kombu.Queue(*args, **kwargs)
    with kombu.Connection(amqp_url) as connection:
        queue(connection).declare()
    return queue


def _register_subscriber(queue, function):
    """Register a function as a subscriber callback for a topic queue.
    """
    _topic_registry.append((queue, function))


def subscribe(topic):
    """Decorate a function to have it act as a callback to messages on a topic.

    The decorated function needs to take two parameters, body and message,
    and is documented in the kombu docs under consumer callbacks.
    """
    def __create_queue_name(func, topic):
        return '{}.{}::{}'.format(func.__module__, func.__name__, topic)

    def wrapper(func):
        # Create Queue from topic.
        model_exchange = kombu.Exchange(
            get_config_param(MODEL_EXCHANGE), 'topic')
        queue_name = __create_queue_name(func, topic)
        queue = _create_or_verify_queue(
            queue_name, exchange=model_exchange, routing_key=topic)

        # Make sure message is acked after callback is executed.
        @wraps(func)
        def new_func(body, message):
            r = func(body, message)
            message.ack()
            return r

        # Register the function to the queue in global registry.
        _register_subscriber(queue, new_func)
        return new_func

    return wrapper


def _drain_all_events(connection, timeout):
    """Drain events in all queues until timeout seconds with no events.
    """
    while True:
        try:
            connection.drain_events(timeout=timeout)
        except socket.timeout:
            break


def drain():
    """Consume all registered queues and execute all subscribed actions.
    """
    with kombu.Connection(get_config_param(AMQP_URL)) as connection:
        # Connect all of the registered queues.
        for q, _ in _topic_registry:
            q(connection).declare()

        # Set up the consumers in preparation for the drain. Consumers need to
        # stay in scope until the drain loop is complete.
        consumers = []
        for q, f in _topic_registry:
            consumer = connection.Consumer(q, callbacks=[f])
            consumer.consume()
            consumers.append(consumer)

        # Keep grabbing things out of the channel until IDLE_TIMEOUT seconds
        # elapse without any events.
        IDLE_TIMEOUT = 2  # seconds
        _drain_all_events(connection, IDLE_TIMEOUT)
