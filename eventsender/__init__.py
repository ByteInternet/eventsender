import json
import os
from collections import namedtuple

import pika
import datetime
from contextlib import closing, contextmanager


CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 1.0


class ImproperlyConfigured(ImportError):
    """ eventsender is somehow improperly configured. """


Settings = namedtuple('Settings', ('EVENT_QUEUE_URL', 'EVENT_QUEUE_EXCHANGE', 'EVENT_QUEUE_ROUTING_KEY'))


def get_settings():
    try:
        # Django is not a dependency, but let's allow for simple integration with Django projects
        from django.conf import settings
        return settings
    except ImportError:
        return Settings(
            os.environ.get("EVENT_QUEUE_URL"),
            os.environ.get("EVENT_QUEUE_EXCHANGE"),
            os.environ.get("EVENT_QUEUE_ROUTING_KEY")
        )


@contextmanager
def open_channel(event_queue_url):
    params = pika.URLParameters(event_queue_url)
    params.connection_attempts = CONNECTION_ATTEMPTS
    params.socket_timeout = CONNECTION_TIMEOUT
    with closing(pika.BlockingConnection(params)) as conn:
        yield conn.channel()


class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)

utc = UTC()


def send_event(event, exchange=None, routing_key=None):
    """
    Add a timestamp to the event data and send it to a message queue
    :param dict event: JSON-serialisable dictionary
    :param str exchange: Exchange to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    :param str routing_key: Routing key to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    If this is not set, use blank by default.
    """
    settings = get_settings()
    exchange = exchange or settings.EVENT_QUEUE_EXCHANGE
    routing_key = routing_key or getattr(settings, 'EVENT_QUEUE_ROUTING_KEY', '')

    if not settings.EVENT_QUEUE_URL:
        raise ImproperlyConfigured('EVENT_QUEUE_URL is not configured in settings')
    if not exchange:
        raise ImproperlyConfigured('EVENT_QUEUE_EXCHANGE is not configured in settings '
                                   'and no exchange provided in parameters.')

    event.update({'timestamp': datetime.datetime.now(tz=utc).isoformat()})
    with open_channel(settings.EVENT_QUEUE_URL) as channel:
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json')
        )
