from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import kombu
from kombu.pools import connections

from . import AMQP_URL, MODEL_EXCHANGE, get_config_param, get_connection


def routing_key(model_name, event_name):
    return '{}.{}'.format(model_name, event_name)


def payload(obj):
    return {'object': obj}


def _create_or_verify_model_exchange(connection):
    """Create or verify existence of model exchange on AMQP server.
    """
    model_exchange = kombu.Exchange(
        get_config_param(MODEL_EXCHANGE), 'topic', connection, durable=True)
    model_exchange.declare()
    return model_exchange


def _publish_to_exchange_topic(connection, exchange, topic, obj):
    """Publish the update object to a specific topic on a topic exchange.
    """
    producer = connection.Producer(serializer='json')
    producer.publish(payload(obj), exchange=exchange, routing_key=topic)


def publish_model_event(model_name, event_name, obj):
    """Send a model event to the pubsub exchange.
    """
    topic = routing_key(model_name, event_name)
    connection = get_connection()
    with connections[connection].acquire(block=True) as conn:
        model_exchange = _create_or_verify_model_exchange(conn)
        _publish_to_exchange_topic(conn, model_exchange, topic, obj)
