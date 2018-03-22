from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import pytest

import kombu
import mock
from pubsub import PubSub

from . import kombu_mock


@pytest.fixture
def pubsub():
    return PubSub("test", "test")


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

    assert len(pubsub.consumers) == 0

    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe(topic)(func)

    assert len(pubsub.consumers) == 1

    consumer = pubsub.consumers[0]
    assert consumer.queue.routing_key == topic


def test_subscribe_adds_to_registry(pubsub):
    with kombu_mock.patch(kombu, pubsub):
        pubsub.subscribe('TestModel.cancelled')(func)

    assert func.__name__ == pubsub.consumers[0].callback.__name__


@mock.patch('pubsub.drain_all_events')
def test_drain_queue(mock_drain_all_events, pubsub):
    with kombu_mock.patch(kombu, pubsub):
        pubsub.drain()

    mock_drain_all_events.assert_called_once()
