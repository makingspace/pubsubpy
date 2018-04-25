from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import contextlib

import mock


class Pool(object):
    def __init__(self, connection, limit=None):
        self.connection = connection
        self.limit = limit

    def acquire(self, block=True):
        return self.connection


class Connection(object):

    last_connection = None

    def __init__(self, url):
        self.url = url
        self.producer = mock.MagicMock()
        self.consumer = mock.MagicMock()

    def __enter__(self, *args, **kwargs):
        Connection.last_connection = self
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def drain_events(self, timeout=None):
        import socket
        raise socket.timeout

    def exchange_declare(self, *args, **kwargs):
        pass

    def queue_declare(self, *args, **kwargs):
        pass

    def queue_bind(self, *args, **kwargs):
        pass

    def prepare_queue_arguments(self, *args, **kwargs):
        return []

    def Producer(self, *args, **kwargs):
        return self.producer

    def Consumer(self, *args, **kwargs):
        return self.consumer

    def Pool(self, limit=None):
        return Pool(self, limit=limit)


Exchange = mock.MagicMock()
Queue = mock.MagicMock()


@contextlib.contextmanager
def patch(kombu_module, pubsub):
    try:
        old_Connection = kombu_module.Connection
        old_Exchange = kombu_module.Connection
        old_Queue = kombu_module.Queue
        kombu_module.Connection = Connection
        kombu_module.Exchange = Exchange
        kombu_module.Queue = Queue
        kombu_module.Exchange.reset_mock()
        kombu_module.Queue.reset_mock()
        pubsub.connection = Connection(pubsub.amqp_url)
        yield
    finally:
        kombu_module.Connection = old_Connection
        kombu_module.Exchange = old_Exchange
        kombu_module.Queue = old_Queue
