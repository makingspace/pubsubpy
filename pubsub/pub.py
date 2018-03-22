from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


def routing_key(model_name, event_name):
    return '{}.{}'.format(model_name, event_name)


def payload(obj):
    return {'object': obj}
