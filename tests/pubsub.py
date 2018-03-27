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

_NAMESPACE = "namespace"

@pytest.fixture
def namespaced_pubsub():
    app = PubSub("test", "test", namespace=_NAMESPACE)
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

    assert len(pubsub.consumer_manager.callback_pairs) == 0

    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe(topic)(func)

    assert len(pubsub.consumer_manager.callback_pairs) == 1

    queue = pubsub.consumer_manager.callback_pairs[0][0]
    assert queue.routing_key == topic


def test_subscribe_adds_to_registry(pubsub):
    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe('TestModel.cancelled')(func)

    assert func.__name__ == pubsub.consumer_manager.callback_pairs[0][1].__name__

def test_namespacing(namespaced_pubsub):
    assert namespaced_pubsub.namespace == _NAMESPACE

    with kombu_mock.patch(kombu, namespaced_pubsub):
        exchange = namespaced_pubsub._create_or_verify_model_exchange(namespaced_pubsub.acquire())

    assert exchange.name == "{}_{}".format(namespaced_pubsub._model_exchange, _NAMESPACE)
