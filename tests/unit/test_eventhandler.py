import eventsender
import unittest
import mock
import json


class TestEventSender(unittest.TestCase):
    def setUp(self):
        self.data = {'data': {'some_data': [1, 2, 3], 'type': 'some_event'}}
        _event = self.data.copy()
        _event.update({'timestamp': "2016-11-15T14:04:02.941878"})
        self.data_json = json.dumps(_event)

    @mock.patch('eventsender.datetime.datetime')
    @mock.patch('eventsender.settings', EVENT_QUEUE_URL='url', EVENT_QUEUE_EXCHANGE='exchange',
                EVENT_QUEUE_ROUTING_KEY='key')
    @mock.patch('eventsender.pika')
    def test_send_event(self, mock_pika, mock_settings, mock_now):
        _mock_channel = mock_pika.BlockingConnection.return_value.channel.return_value
        _mock_publish = mock.MagicMock()
        _mock_channel.basic_publish = _mock_publish
        mock_now.now.return_value.isoformat.return_value = "2016-11-15T14:04:02.941878"
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
