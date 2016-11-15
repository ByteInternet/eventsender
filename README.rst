===================
eventsender
===================
This is a simple event sender that publishes JSON-serialisable messages to an AMQP server exchange. It can also be optionally installed as a Django application.


Installation and configuration
------------------------------

The following settings should be supplied either as environment variables or via Django settings module:

.. code-block:: python

    EVENT_QUEUE_URL = os.environ.get('EVENT_QUEUE_URL')
    EVENT_QUEUE_EXCHANGE = os.environ.get('EVENT_QUEUE_EXCHANGE')
    EVENT_QUEUE_ROUTING_KEY = os.environ.get('EVENT_QUEUE_ROUTING_KEY', '')


Usage
-----
Example:

.. code-block:: python

    from eventsender import send_event
    send_event({'type': 'user.subscribed', 'username': 'john_doe'})

Or

.. code-block:: bash

   EVENT_QUEUE_EXCHANGE=some_exchange EVENT_QUEUE_URL=amqp://guest:guest@localhost:5672/host python -c \
        "import eventsender; eventsender.send_event({'type': 'event_type', 'somedata': {'key': 'value'}})"


Running tests
-------------
Just run ``nosetests`` to run tests against your current setup.


=====
About
=====
This software is brought to you by Byte, a webhosting provider based in Amsterdam, The Netherlands. We specialize in
fast and secure Magento hosting and scalable cluster hosting.

Check out our `Github page <https://github.com/ByteInternet>`_ for more open source software or `our site <https://www.byte.nl>`_
to learn about our products and technologies. Look interesting? Reach out about `joining the team <https://www.byte.nl/vacatures>`_.
Or just drop by for a cup of excellent coffee if you're in town!
