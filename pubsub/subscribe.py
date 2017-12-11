from __future__ import absolute_import, division, print_function, unicode_literals

from kombu import Connection, Exchange, Queue


AMQP_URL = 'amqp://rzfgdjss:84cYeZtj5J9cb821twXu_R5fSDjRnh2q@spider.rmq.cloudamqp.com/rzfgdjss'
MODEL_EXCHANGE = 'model_event_exchange'

model_exchange = Exchange(MODEL_EXCHANGE, topic, durable=True)

# List of tuples (Queue, Callback)
__topic_registry = []


def subscribe(topic):
    """todo
    """
    def wrapper(func):
        # create Queue from topic
        function_full_name = '{}.{}'.format(func.__module__, func.__name__)
        queue = Queue(function_full_name, exchange=model_exchange, key=topic)
        # register the function to the queue in global registry
        __topic_registry.append((queue, func))
        return func

    return wrapper


def drain():
    """todo
    """
    with Connection(AMQP_URL) as connection:
        for q, _ in __topic_registry:
            q(connection).declare()
        for q, f in __topic_registry:
            with connection.Consumer(q, callbacks=[f]) as consumer:
                consumer.consume()
