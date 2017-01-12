from mock import patch

from eventsender import get_settings
from tests.unit import SenderTestCase


class TestGetSettings(SenderTestCase):

    def test_get_settings_fetches_settings_from_environment_if_django_not_installed(self):
        with patch.dict('os.environ', EVENT_QUEUE_URL='a', EVENT_QUEUE_EXCHANGE='b', EVENT_QUEUE_ROUTING_KEY='c'):
            settings = get_settings()
            self.assertEqual(settings.EVENT_QUEUE_URL, 'a')
            self.assertEqual(settings.EVENT_QUEUE_EXCHANGE, 'b')
            self.assertEqual(settings.EVENT_QUEUE_ROUTING_KEY, 'c')
