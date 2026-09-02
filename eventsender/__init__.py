import json
import os
from collections import namedtuple

import pika
import datetime
from contextlib import closing, contextmanager

from opentelemetry import propagate, trace


CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 1.0

tracer = trace.get_tracer('eventsender')


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


def _resolve_destination(exchange, routing_key):
    """Fill in the exchange and routing key from the settings and check they are usable

    :return tuple: The event queue url, the exchange and the routing key to publish to
    """
    settings = get_settings()
    exchange = exchange or settings.EVENT_QUEUE_EXCHANGE
    routing_key = routing_key or getattr(settings, 'EVENT_QUEUE_ROUTING_KEY', '')

    if not settings.EVENT_QUEUE_URL:
        raise ImproperlyConfigured('EVENT_QUEUE_URL is not configured in settings')
    if not exchange:
        raise ImproperlyConfigured('EVENT_QUEUE_EXCHANGE is not configured in settings '
                                   'and no exchange provided in parameters.')

    return settings.EVENT_QUEUE_URL, exchange, routing_key


def _publish_event(channel, event, exchange, routing_key):
    """Add a timestamp to the event data and publish it on an already opened channel"""
    event.update({'timestamp': datetime.datetime.now(tz=utc).isoformat()})
    with tracer.start_as_current_span('publish {}'.format(exchange), kind=trace.SpanKind.PRODUCER) as span:
        span.set_attribute('messaging.system', 'rabbitmq')
        span.set_attribute('messaging.operation.name', 'publish')
        span.set_attribute('messaging.operation.type', 'send')
        span.set_attribute('messaging.destination.name', exchange)
        if routing_key:
            span.set_attribute('messaging.rabbitmq.destination.routing_key', routing_key)
        if event.get('type'):
            span.set_attribute('event.type', str(event['type']))
        headers = {}
        propagate.inject(headers)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', headers=headers)
        )


def send_event(event, exchange=None, routing_key=None):
    """
    Add a timestamp to the event data and send it to a message queue
    :param dict event: JSON-serialisable dictionary
    :param str exchange: Exchange to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    :param str routing_key: Routing key to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    If this is not set, use blank by default.
    """
    send_events([event], exchange=exchange, routing_key=routing_key)


def send_events(events, exchange=None, routing_key=None):
    """
    Add a timestamp to every event and send them to a message queue over one connection

    Opening an AMQP connection costs a TCP and an AMQP handshake, so publishing a batch
    one event at a time through `send_event` spends most of its time connecting. Every
    event still gets its own timestamp, tracking span and message, so this is only a
    cheaper way to send the same messages.

    :param iterable events: JSON-serialisable dictionaries
    :param str exchange: Exchange to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    :param str routing_key: Routing key to use. If not set will default to EVENT_QUEUE_EXCHANGE setting.
    If this is not set, use blank by default.
    """
    event_queue_url, exchange, routing_key = _resolve_destination(exchange, routing_key)

    events = list(events)
    if not events:
        return

    with open_channel(event_queue_url) as channel:
        for event in events:
            _publish_event(channel, event, exchange, routing_key)
