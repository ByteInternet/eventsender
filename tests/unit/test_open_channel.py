from eventsender import open_channel
from tests.unit import SenderTestCase


class TestOpenChannel(SenderTestCase):
    def setUp(self):
        self.set_up_settings()
        self.mock_connection = self.set_up_patch('pika.BlockingConnection')

    def test_open_channel_returns_pika_channel(self):
        mock_channel = self.mock_connection().channel()

        with open_channel("amqp://host/url") as channel:
            self.assertEqual(channel, mock_channel)

    def test_open_channel_sets_correct_pika_parameters(self):
        with open_channel("amqp://host/url") as channel:
            # test if the connection was set up properly
            _, args, _ = self.mock_connection.mock_calls[0]
            params = args[0]
            self.assertEqual(params.connection_attempts, 3)
            self.assertEqual(params.socket_timeout, 1)
            self.assertEqual(params.host, "host")
