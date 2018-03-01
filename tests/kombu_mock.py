from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from functools import wraps

import mock


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
        return None

    def drain_events(self):
        import socket
        raise socket.timeout

    def Producer(self, *args, **kwargs):
        return self.producer

    def Consumer(self, *args, **kwargs):
        return self.consumer


Exchange = mock.MagicMock()
Queue = mock.MagicMock()


def patch(kombu_module):
    def decorator(func):
        @wraps(func)
        def wrapper(self):
            from pubsub import __GLOBAL_CONFIG, CONNECTION, AMQP_URL
            try:
                old_Connection = kombu_module.Connection
                old_Exchange = kombu_module.Connection
                old_Queue = kombu_module.Queue
                kombu_module.Connection = Connection
                kombu_module.Exchange = Exchange
                kombu_module.Queue = Queue
                kombu_module.Exchange.reset_mock()
                kombu_module.Queue.reset_mock()
                __GLOBAL_CONFIG[CONNECTION] = Connection(__GLOBAL_CONFIG[AMQP_URL])
                func(self)
            finally:
                kombu_module.Connection = old_Connection
                kombu_module.Exchange = old_Exchange
                kombu_module.Queue = old_Queue

        return wrapper

    return decorator
