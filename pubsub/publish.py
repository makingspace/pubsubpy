from __future__ import absolute_import, division, print_function, unicode_literals

from kombu import Connection, Exchange

AMQP_URL = 'amqp://rzfgdjss:84cYeZtj5J9cb821twXu_R5fSDjRnh2q@spider.rmq.cloudamqp.com/rzfgdjss'
MODEL_EXCHANGE = 'model_event_exchange'


def routing_key(model_name, event_name):
    return '{}.{}'.format(model_name, event_name)


def payload(obj):
    return {'object': obj}


def publish_model_event(model_name, event_name, obj):
    """Send a model event to the pubsub exchange.
    """
    topic = routing_key(model_name, event_name)
    with Connection(AMQP_URL) as connection:
        model_exchange = Exchange(MODEL_EXCHANGE, 'topic', connection, durable=True)
        model_exchange.declare()
        producer = connection.Producer(serializer='json')
        producer.publish(payload(obj), exchange=model_exchange, routing_key=topic)
