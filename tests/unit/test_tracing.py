import eventsender
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind

from tests.unit import SenderTestCase


class TracingTestCase(SenderTestCase):
    def setUp(self):
        self.set_up_settings()
        self.mock_open_channel = self.set_up_patch('eventsender.open_channel')
        self.mock_channel = self.mock_open_channel().__enter__()
        self.set_up_patch('pika.BasicProperties', side_effect=lambda **params: params)

    def get_published_headers(self):
        _, kwargs = self.mock_channel.basic_publish.call_args
        return kwargs['properties']['headers']


class TestSendEventWithoutTracingConfigured(TracingTestCase):
    def test_message_headers_are_empty(self):
        eventsender.send_event({'type': 'some_event'})

        self.assertEqual(self.get_published_headers(), {})


class TestSendEventWithTracingConfigured(TracingTestCase):
    def setUp(self):
        super().setUp()
        self.exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.set_up_patch('eventsender.tracer', provider.get_tracer('test'))

    def test_injects_trace_context_into_message_headers(self):
        eventsender.send_event({'type': 'some_event'})

        headers = self.get_published_headers()
        span = self.exporter.get_finished_spans()[0]
        self.assertIn('traceparent', headers)
        self.assertIn('{:032x}'.format(span.context.trace_id), headers['traceparent'])

    def test_injected_context_points_at_the_publish_span(self):
        eventsender.send_event({'type': 'some_event'})

        headers = self.get_published_headers()
        span = self.exporter.get_finished_spans()[0]
        self.assertIn('{:016x}'.format(span.context.span_id), headers['traceparent'])

    def test_creates_producer_span_with_messaging_attributes(self):
        eventsender.send_event({'type': 'some_event'})

        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(span.name, 'publish exchange')
        self.assertEqual(span.kind, SpanKind.PRODUCER)
        self.assertEqual(span.attributes['messaging.system'], 'rabbitmq')
        self.assertEqual(span.attributes['messaging.operation.name'], 'publish')
        self.assertEqual(span.attributes['messaging.operation.type'], 'send')
        self.assertEqual(span.attributes['messaging.destination.name'], 'exchange')
        self.assertEqual(span.attributes['messaging.rabbitmq.destination.routing_key'], 'key')
        self.assertEqual(span.attributes['event.type'], 'some_event')
