from __future__ import absolute_import, division, print_function, unicode_literals

from functools import wraps
import socket

from kombu import Connection, Exchange, Queue


AMQP_URL = 'amqp://rzfgdjss:84cYeZtj5J9cb821twXu_R5fSDjRnh2q@spider.rmq.cloudamqp.com/rzfgdjss'
MODEL_EXCHANGE = 'model_event_exchange'

g_model_exchange = Exchange(MODEL_EXCHANGE, 'topic')

# List of tuples (Queue, Callback)
__topic_registry = []


def subscribe(topic):
    """Decorate a function to have it act as a callback to messages on a topic.

    The decorated function needs to take two parameters, body and message,
    and is documented in the kombu docs under consumer callbacks.
    """
    def wrapper(func):
        # Create Queue from topic.
        queue_name = '{}.{}::{}'.format(func.__module__, func.__name__, topic)
        queue = Queue(queue_name, exchange=g_model_exchange, routing_key=topic)

        # Make sure the queue is created on the AMQP server.
        with Connection(AMQP_URL) as connection:
            queue(connection).declare()

        # Make sure message is acked after callback is executed.
        @wraps(func)
        def new_func(body, message):
            r = func(body, message)
            message.ack()
            return r

        # Register the function to the queue in global registry.
        __topic_registry.append((queue, new_func))
        return new_func

    return wrapper


def drain():
    """Consume all registered queues and execute all subscribed actions.
    """
    with Connection(AMQP_URL) as connection:
        # Connect all of the registered queues.
        for q, _ in __topic_registry:
            q(connection).declare()

        # Set up the consumers in preparation for the drain. Consumers need to
        # stay in scope until the drain loop is complete.
        consumers = []
        for q, f in __topic_registry:
            consumer = connection.Consumer(q, callbacks=[f])
            consumer.consume()
            consumers.append(consumer)

        # Keep grabbing things out of the channel until IDLE_TIMEOUT seconds
        # elapse without any events.
        IDLE_TIMEOUT = 2  # seconds
        while True:
            try:
                connection.drain_events(timeout=IDLE_TIMEOUT)
            except socket.timeout:
                break
