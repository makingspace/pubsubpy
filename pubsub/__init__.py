from __future__ import division, print_function, unicode_literals

import logging
import os
import importlib
import socket

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin
from kombu.pools import connections as kombu_connection_pools

from .pub import payload, routing_key

AMQP_URL = 'amqp_url'
MODEL_EXCHANGE = 'model_exchange'
CONNECTION = "__connection"
PUBSUB_VERBOSITY = "PUBSUB_VERBOSITY"

__OPTIONAL_INIT_KWARGS = set()


class PubSubVerbosity:

    NONE = 0
    NORMAL = 1
    DEBUG = 2

    _labels = {NONE: "NONE", NORMAL: "NORMAL", DEBUG: "DEBUG"}

    _reverse = {v: k for k, v in _labels.items()}

    _values = {NONE, NORMAL, DEBUG}

    @classmethod
    def get_verbosity(cls):
        verbosity = cls.NORMAL

        if PUBSUB_VERBOSITY in os.environ:
            verbosity_environment_setting = os.environ.get(PUBSUB_VERBOSITY)
            if verbosity_environment_setting in cls._values:
                verbosity = verbosity_environment_setting
            else:
                lookup = cls._reverse.get(
                    verbosity_environment_setting.upper())
                if lookup:
                    verbosity = lookup

        return verbosity


class PubSubConsumerManager(ConsumerMixin):
    """
    Object that governs draining events associated with subscribed queues.

    Manages a list of topics and callbacks, and implements the get_consumers()
    API to generate one kombu.Consumer for each pair.
    """

    def __init__(self, pubsub):
        self.pubsub = pubsub

        self.connection = pubsub.connection
        self.callback_pairs = []

    def add_callback(self, queue, callback):
        self.callback_pairs.append((queue, callback))

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(queues=[queue], callbacks=[callback, self.ack])
            for queue, callback in self.callback_pairs
        ]

    def ack(self, body, message):
        if self.pubsub.verbosity == PubSubVerbosity.DEBUG:
            self.pubsub.logger.debug("{} ACK".format(message))

        message.ack()

    def declare(self, connection):
        # Connect all of the registered queues.
        for queue, _ in self.callback_pairs:
            queue(connection).declare()

    TOKENS = 1
    IDLE_TIMEOUT = 2

    def drain(self):
        """
        Run inner loop of run() exactly once.
        """
        if self.restart_limit.can_consume(self.TOKENS):
            try:
                for _ in self.consume(limit=None, timeout=self.IDLE_TIMEOUT):
                    pass
            except socket.timeout:
                return

    def __repr__(self):
        return "PubSubConsumerManager: {}".format(", ".join(
            queue.name for queue, _ in self.callback_pairs))


logging.basicConfig()


class PubSub(object):
    """
    Manager for PubSub publishing and consuming.
    """

    def __init__(self,
                 amqp_url=None,
                 model_exchange="model_event_exchange",
                 namespace="",
                 **kwargs):
        if not (amqp_url and model_exchange):
            raise ValueError("Required parameters: amqp_url, model_exchange")

        self.amqp_url = amqp_url
        self.namespace = namespace
        self._model_exchange = model_exchange
        self.connection = self._new_connection()
        self.config = {
            k: v
            for k, v in kwargs.items() if k in __OPTIONAL_INIT_KWARGS
        }

        self.consumer_manager = PubSubConsumerManager(self)

        self.verbosity = PubSubVerbosity.get_verbosity()
        self.logger = logging.getLogger("{}.{}".format(
            __name__, self.__class__.__name__))

    @property
    def model_exchange(self):
        return self._model_exchange if not self.namespace else "{}_{}".format(
            self._model_exchange, self.namespace)

    def _new_connection(self):
        return Connection(self.amqp_url)

    def import_subscribers(self, dot_paths):
        """
        Convenience method to ensure that all subscriber-decorated functions
        are registered. Accepts a list of dot-paths to modules containing
        subscriber functions.
        """
        for dot_path in dot_paths:
            importlib.import_module(dot_path)

    def acquire(self):
        if self.verbosity == PubSubVerbosity.DEBUG:
            self.logger.debug("Acquiring connection.")

        return kombu_connection_pools[self.connection].acquire(block=True)

    def _register_subscriber(self, queue, function):
        """
        Register a function as a subscriber callback for a topic queue.
        """
        log = self.verbosity > PubSubVerbosity.NONE
        if log:
            self.logger.info(
                "Registering subscriber function {} to queue {}".format(
                    function, queue))

        self.consumer_manager.add_callback(queue, function)

        if log:
            self.logger.debug("Now {} consumers registered.".format(
                len(self.consumer_manager.callback_pairs)))

    def _create_or_verify_model_exchange(self, connection):
        """
        Create or verify existence of model exchange on AMQP server.
        """
        model_exchange = Exchange(
            self.model_exchange, 'topic', connection, durable=True)
        model_exchange.declare()
        return model_exchange

    def _create_or_verify_queue(self, queue_name, *args, **kwargs):
        """
        Create or verify existence of queue on AMQP server.
        """
        queue = Queue(queue_name, *args, **kwargs)
        with self.acquire() as conn:
            queue(conn).declare()
        return queue

    def subscribe(self, topic):
        """
        Decorate a function to have it act as a callback to messages on a topic.

        The decorated function needs to take two parameters, body and message,
        and is documented in the kombu docs under consumer callbacks.
        """

        def __create_queue_name(func, topic):
            namespace = "[{}]".format(self.namespace) if self.namespace else ""
            return '{}{}.{}::{}'.format(namespace, func.__module__,
                                        func.__name__, topic)

        def wrapper(func):
            queue_name = __create_queue_name(func, topic)
            model_exchange = Exchange(self.model_exchange, 'topic')
            # Create Queue from topic.
            queue = self._create_or_verify_queue(
                queue_name, exchange=model_exchange, routing_key=topic)

            # Register the function to the queue in object registry.
            self._register_subscriber(queue, func)

            if self.verbosity == PubSubVerbosity.DEBUG:
                self.logger.info("Subscribing function {} to queue {}.".format(
                    func.__name__, queue.name))

            return func

        return wrapper

    def drain(self):
        """
        Consume all registered queues and execute all subscribed actions.
        """
        if self.verbosity == PubSubVerbosity.DEBUG:
            self.logger.debug("Draining.")

        with self.acquire() as connection:
            self.consumer_manager.declare(connection)
            # NOTE: Is it a problem that we don't pass connection in to drain()?
            self.consumer_manager.drain()

    def _publish_to_exchange_topic(self, connection, exchange, topic, obj):
        """
        Publish the update object to a specific topic on a topic exchange.
        """
        producer = self.connection.Producer(serializer='json')
        producer.publish(payload(obj), exchange=exchange, routing_key=topic)

    def publish_model_event(self, model_name, event_name, obj):
        """
        Send a model event to the pubsub exchange.
        """
        topic = routing_key(model_name, event_name)

        if self.verbosity == PubSubVerbosity.DEBUG:
            self.logger.debug("Publishing model event: {}".format(topic))

        with self.acquire() as connection:
            model_exchange = self._create_or_verify_model_exchange(connection)
            self._publish_to_exchange_topic(connection, model_exchange, topic,
                                            obj)
