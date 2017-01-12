from unittest import TestCase
from mock import MagicMock, patch
from eventsender import Settings


class SenderTestCase(TestCase):
    def set_up_patch(self, topatch, themock=None, **kwargs):
        """
        Patch a function or class
        :param topatch: string The class to patch
        :param themock: optional object to use as mock
        :return: mocked object
        """
        if themock is None:
            themock = MagicMock(**kwargs)

        patcher = patch(topatch, themock)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def set_up_settings(self):
        self.mock_settings = Settings('amqp://host/url', 'exchange', 'key')
        self.set_up_patch('eventsender.get_settings', return_value=self.mock_settings)
