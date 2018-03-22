from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import socket


def drain_all_events(connection, timeout):
    """Drain events in all queues until timeout seconds with no events.
    """
    while True:
        try:
            connection.drain_events(timeout=timeout)
        except socket.timeout:
            break
