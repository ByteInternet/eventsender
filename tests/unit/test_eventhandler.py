import eventsender
import unittest
import mock
import json


class TestEventSender(unittest.TestCase):
    def setUp(self):
        self.data = {'type': 'some_event', 'data': {'some_data': [1, 2, 3]}}
        self.data_json = json.dumps(self.data)

    @mock.patch('eventsender.settings', EVENT_QUEUE_URL='url', EVENT_QUEUE_EXCHANGE='exchange',
                EVENT_QUEUE_ROUTING_KEY='key')
    @mock.patch('eventsender.pika')
    def test_send_event(self, mock_pika, mock_settings):
        _mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value
        _mock_publish = mock.MagicMock()
        _mock_channel.basic_publish = _mock_publish
        eventsender.send_event(self.data)
        _mock_publish.assert_called_once_with(
            exchange='exchange', routing_key='key', body=self.data_json,
            properties=mock_pika.BasicProperties(delivery_mode=2, content_type='application/json'))

    @mock.patch('eventsender.settings', EVENT_QUEUE_EXCHANGE='exchange')
    @mock.patch('eventsender.pika')
    def test_raise_url_improperly_configured(self, mock_pika, mock_settings):
        self.assertRaises(eventsender.send_event(self.data))

    @mock.patch('eventsender.settings', EVENT_QUEUE_URL='url')
    @mock.patch('eventsender.pika')
    def test_raise_exchange_improperly_condigured(self, mock_pika, mock_settings):
        self.assertRaises(eventsender.send_event(self.data))
