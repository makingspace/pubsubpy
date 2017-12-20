from __future__ import absolute_import, division, print_function, unicode_literals

import kombu

AMQP_URL = 'amqp://rzfgdjss:84cYeZtj5J9cb821twXu_R5fSDjRnh2q@spider.rmq.cloudamqp.com/rzfgdjss'
MODEL_EXCHANGE = 'model_event_exchange'


def routing_key(model_name, event_name):
    return '{}.{}'.format(model_name, event_name)


def payload(obj):
    return {'object': obj}


def _create_or_verify_model_exchange(connection):
    """Create or verify existence of model exchange on AMQP server.
    """
    model_exchange = kombu.Exchange(MODEL_EXCHANGE, 'topic', connection, durable=True)
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
    with kombu.Connection(AMQP_URL) as connection:
        model_exchange = _create_or_verify_model_exchange(connection)
        _publish_to_exchange_topic(connection, model_exchange, topic, obj)
