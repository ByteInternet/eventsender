import datetime
from unittest.mock import Mock

import pika
import eventsender
import json

from eventsender import Settings, ImproperlyConfigured

from tests.unit import SenderTestCase


class TestEventSender(SenderTestCase):
    def setUp(self):
        self.set_up_settings()

        # mock datetime, so we can match the date
        self.now = datetime.datetime.now(tz=eventsender.utc)
        self.mock_datetime = self.set_up_patch('datetime.datetime')
        self.mock_datetime.now.return_value = self.now

        # mock channels
        self.mock_open_channel = self.set_up_patch('eventsender.open_channel')
        self.mock_channel = self.mock_open_channel().__enter__()

        # mock BasicProperties, because they do not compare well with identical properties
        self.mock_basic_properties = self.set_up_patch('pika.BasicProperties', side_effect=lambda **params: params)

    def test_sends_event(self):
        data = {'data': {'some_data': [1, 2, 3], 'type': 'some_event'}}
        expected_post_data = dict(data, timestamp=self.now.isoformat())

        eventsender.send_event(data)
        self.mock_channel.basic_publish.assert_called_once_with(
            exchange='exchange',
            routing_key='key',
            body=json.dumps(expected_post_data),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))

    def test_utc_timezone_is_correctly_offset(self):
        self.assertTrue(self.now.isoformat().endswith("+00:00") or self.now.isoformat().endswith("Z"))

    def test_send_event_sends_utc_timestamp(self):
        eventsender.send_event({})
        self.mock_datetime.now.assert_called_once_with(tz=eventsender.utc)

    def test_raise_url_improperly_configured(self):
        mock_settings = Settings(None, 'exchange', 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)
        with self.assertRaises(ImproperlyConfigured):
            eventsender.send_event({})

    def test_raise_exchange_improperly_configured(self):
        mock_settings = Settings('amqp://host/url', None, 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)
        with self.assertRaises(ImproperlyConfigured):
            eventsender.send_event({})

    def test_does_not_raise_exchange_improperly_configured_if_no_setting_but_param_provided(self):
        mock_settings = Settings('amqp://host/url', None, 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        eventsender.send_event({}, "my_exchange")

    def test_send_event_uses_provided_exchange_parameter(self):
        eventsender.send_event({}, "my_exchange")

        self.mock_channel.basic_publish.assert_called_once_with(
            exchange='my_exchange',
            routing_key='key',
            body=json.dumps(dict({}, timestamp=self.now.isoformat())),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))

    def test_send_event_exchange_parameter_takes_precedence_over_exchange_setting(self):
        mock_settings = Settings('amqp://host/url', "other_exchange", 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        eventsender.send_event({}, "my_exchange")

        self.mock_channel.basic_publish.assert_called_once_with(
            exchange='my_exchange',
            routing_key='key',
            body=json.dumps(dict({}, timestamp=self.now.isoformat())),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))

    def test_send_event_routing_key_takes_precendence_over_exchange_setting(self):
        mock_settings = Settings('amqp://host/url', "exchange", 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        eventsender.send_event({}, routing_key="my_key")

        self.mock_channel.basic_publish.assert_called_once_with(
            exchange='exchange',
            routing_key='my_key',
            body=json.dumps(dict({}, timestamp=self.now.isoformat())),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))

    def test_uses_blank_routing_key_if_no_setting_and_no_parameter_provided(self):
        class NoKeySettings:
            EVENT_QUEUE_URL = None
            EVENT_QUEUE_EXCHANGE = None

            def __init__(self, event_queue_url, event_queue_exchange):
                self.EVENT_QUEUE_URL= event_queue_url
                self.EVENT_QUEUE_EXCHANGE= event_queue_exchange

        mock_settings = NoKeySettings('amqp://host/url', "exchange")
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        eventsender.send_event({})

        self.mock_channel.basic_publish.assert_called_once_with(
            exchange='exchange',
            routing_key='',
            body=json.dumps(dict({}, timestamp=self.now.isoformat())),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))


class TestSendEvents(SenderTestCase):
    def setUp(self):
        self.set_up_settings()

        # mock datetime, so we can match the date
        self.now = datetime.datetime.now(tz=eventsender.utc)
        self.mock_datetime = self.set_up_patch('datetime.datetime')
        self.mock_datetime.now.return_value = self.now

        # mock channels
        self.mock_open_channel = self.set_up_patch('eventsender.open_channel')
        self.mock_channel = self.mock_open_channel().__enter__()
        self.mock_open_channel.reset_mock()

        # mock BasicProperties, because they do not compare well with identical properties
        self.mock_basic_properties = self.set_up_patch('pika.BasicProperties', side_effect=lambda **params: params)

    def published_bodies(self):
        return [kwargs['body'] for _, kwargs in self.mock_channel.basic_publish.call_args_list]

    def test_opens_one_connection_for_all_events(self):
        eventsender.send_events([{'type': 'one'}, {'type': 'two'}, {'type': 'three'}])

        self.mock_open_channel.assert_called_once_with('amqp://host/url')

    def test_publishes_every_event(self):
        eventsender.send_events([{'type': 'one'}, {'type': 'two'}])

        self.assertEqual(
            self.published_bodies(),
            [
                json.dumps({'type': 'one', 'timestamp': self.now.isoformat()}),
                json.dumps({'type': 'two', 'timestamp': self.now.isoformat()}),
            ])

    def test_publishes_every_event_to_the_configured_destination(self):
        eventsender.send_events([{'type': 'one'}, {'type': 'two'}])

        for _, kwargs in self.mock_channel.basic_publish.call_args_list:
            self.assertEqual(kwargs['exchange'], 'exchange')
            self.assertEqual(kwargs['routing_key'], 'key')
            self.assertEqual(
                kwargs['properties'],
                pika.BasicProperties(delivery_mode=2, content_type='application/json', headers={}))

    def test_uses_provided_exchange_and_routing_key(self):
        eventsender.send_events([{'type': 'one'}], 'my_exchange', 'my_key')

        _, kwargs = self.mock_channel.basic_publish.call_args
        self.assertEqual(kwargs['exchange'], 'my_exchange')
        self.assertEqual(kwargs['routing_key'], 'my_key')

    def test_accepts_any_iterable_of_events(self):
        eventsender.send_events(event for event in [{'type': 'one'}, {'type': 'two'}])

        self.assertEqual(self.mock_channel.basic_publish.call_count, 2)

    def test_does_not_open_a_connection_without_events(self):
        eventsender.send_events([])

        self.mock_open_channel.assert_not_called()
        self.mock_channel.basic_publish.assert_not_called()

    def test_raises_url_improperly_configured_even_without_events(self):
        mock_settings = Settings(None, 'exchange', 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        with self.assertRaises(ImproperlyConfigured):
            eventsender.send_events([])

    def test_raises_exchange_improperly_configured(self):
        mock_settings = Settings('amqp://host/url', None, 'key')
        self.set_up_patch('eventsender.get_settings', return_value=mock_settings)

        with self.assertRaises(ImproperlyConfigured):
            eventsender.send_events([{'type': 'one'}])

    def test_send_event_publishes_through_send_events(self):
        eventsender.send_event({'type': 'one'})

        self.mock_open_channel.assert_called_once_with('amqp://host/url')
        self.assertEqual(
            self.published_bodies(),
            [json.dumps({'type': 'one', 'timestamp': self.now.isoformat()})])
