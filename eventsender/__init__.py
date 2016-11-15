import json
import pika
import datetime
from contextlib import closing

try:
    # django is not a dependency, but let's allow for easy integrating with Django projects
    from django.conf import settings
except ImportError:
    import settings


CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 1.0


class ImproperlyConfigured(ImportError):
    """ eventsender is somehow improperly configured. """


def send_event(event):
    """
    Add a timestamp to the event data and send it to a message queue
    :param dict event: JSON-serialisable dictionary
    """
    if not settings.EVENT_QUEUE_URL:
        raise ImproperlyConfigured('EVENT_QUEUE_URL is not configured in settings')
    if not settings.EVENT_QUEUE_EXCHANGE:
        raise ImproperlyConfigured('EVENT_QUEUE_EXCHANGE is not configured in settings')

    event.update({'timestamp': datetime.datetime.now().isoformat()})
    params = pika.URLParameters(settings.EVENT_QUEUE_URL)
    params.connection_attempts = CONNECTION_ATTEMPTS
    params.socket_timeout = CONNECTION_TIMEOUT
    with closing(pika.BlockingConnection(params)) as conn:
        chan = conn.channel()
        chan.basic_publish(
            exchange=settings.EVENT_QUEUE_EXCHANGE,
            routing_key=getattr(settings, 'EVENT_QUEUE_ROUTING_KEY', ''),
            body=json.dumps(event),
            properties=pika.BasicProperties(delivery_mode=2, content_type='application/json')
        )
