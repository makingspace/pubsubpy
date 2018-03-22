from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import pytest

import kombu
from pubsub import PubSub, PubSubVerbosity

from . import kombu_mock


@pytest.fixture
def pubsub():
    app = PubSub("test", "test")
    app.verbosity = PubSubVerbosity.DEBUG

    return app


def test_publish_model_event(pubsub):
    model_name = 'TestModel'
    event_name = 'cancelled'
    obj = {'a': 1, 'b': [2, 3], 'c': {'key': 'value'}}

    with kombu_mock.patch(kombu, pubsub):
        pubsub.publish_model_event(model_name, event_name, obj)
        mock_publish = kombu.Connection.last_connection.producer.publish

    mock_publish.assert_called_once()
    assert {'object': obj} in mock_publish.call_args[0]
    assert ('routing_key',
            'TestModel.cancelled') in mock_publish.call_args[1].items()


def func(b, m):
    return None


def test_subscribe_creates_queue(pubsub):
    topic = 'TestModel.cancelled'

    assert len(pubsub.consumer_manager.queues) == 0

    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe(topic)(func)

    assert len(pubsub.consumer_manager.queues) == 1

    queue = pubsub.consumer_manager.queues[0]
    assert queue.routing_key == topic


def test_subscribe_adds_to_registry(pubsub):
    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe('TestModel.cancelled')(func)

    assert func.__name__ == pubsub.consumer_manager.callbacks[0].__name__
