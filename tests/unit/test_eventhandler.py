import datetime

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
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json'))

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
