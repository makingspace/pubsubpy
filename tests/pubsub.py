from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase

import kombu
import mock

import pubsub

from . import kombu_mock


class PubsubTestBase(TestCase):
    def setUp(self):
        setattr(pubsub, '__GLOBAL_CONFIG', {
            'amqp_url': 'test',
            'model_exchange': 'test',
        })


class PublishTests(PubsubTestBase):
    @kombu_mock.patch(kombu)
    def test_publish_model_event(self):
        model_name = 'TestModel'
        event_name = 'cancelled'
        obj = {'a': 1, 'b': [2, 3], 'c': {'key': 'value'}}
        pubsub.publish_model_event(model_name, event_name, obj)
        mock_publish = kombu.Connection.last_connection.producer.publish
        mock_publish.assert_called_once()
        self.assertIn({'object': obj}, mock_publish.call_args[0])
        self.assertIn(('routing_key', 'TestModel.cancelled'),
                      mock_publish.call_args[1].items())


def func(b, m):
    return None


class SubscribeTests(PubsubTestBase):
    @kombu_mock.patch(kombu)
    def test_subscribe_creates_queue(self):
        pubsub.subscribe('TestModel.cancelled')(func)
        kombu.Queue.assert_called_once()
        self.assertIn(('routing_key', 'TestModel.cancelled'),
                      kombu.Queue.call_args[1].items())

    @kombu_mock.patch(kombu)
    def test_subscribe_adds_to_registry(self):
        pubsub.subscribe('TestModel.cancelled')(func)
        self.assertEquals(func.__name__,
                          pubsub.sub._topic_registry[0][1].__name__)


class DrainTests(TestCase):
    @kombu_mock.patch(kombu)
    @mock.patch('pubsub.sub._drain_all_events')
    def test_drain_queue(self, mock_drain_all_events):
        pubsub.drain()
        mock_drain_all_events.assert_called_once()
