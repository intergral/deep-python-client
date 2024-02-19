#       Copyright (C) 2024  Intergral GmbH
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import unittest

import mockito
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider

from deep.api.plugin.otel import OTelPlugin
from deep.api.resource import TELEMETRY_SDK_NAME


class TestOtel(unittest.TestCase):

    def setUp(self):
        resource = Resource(attributes={
            SERVICE_NAME: "your-service-name"
        })
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

    def test_load_plugin(self):
        plugin = OTelPlugin()
        load_plugin = plugin.resource()
        self.assertIsNotNone(load_plugin)
        self.assertEqual("your-service-name", load_plugin.attributes.get(SERVICE_NAME))
        self.assertIsNone(load_plugin.attributes.get(TELEMETRY_SDK_NAME))

    def test_collect_attributes(self):
        with trace.get_tracer_provider().get_tracer("test").start_as_current_span("test-span"):
            plugin = OTelPlugin()

            mock = mockito.mock()
            mock.trigger_context = mock
            mock.trigger_context.id = "id"
            mock.location_action = mock
            mock.location_action.id = "id"
            mock.location_action.location = mock
            mock.location_action.location.name = "test"

            attributes = plugin.decorate("snap_id", mock)
            self.assertIsNotNone(attributes)
            self.assertEqual("test-span", attributes.get("span_name"))
            self.assertIsNotNone(attributes.get("span_id"))
            self.assertIsNotNone(attributes.get("trace_id"))
            self.assertEqual(plugin.current_span().proxy.events[0].name, "test")
            self.assertEqual(plugin.current_span().proxy.events[0].attributes,
                             {'snapshot': 'snap_id', 'tracepoint': 'id', 'context': 'id'})

    def test_create_span(self):
        plugin = OTelPlugin()
        span = plugin.create_span("test", "ctx_id", "tp_id")
        self.assertIsNotNone(span)
        attributes = span.proxy.attributes
        self.assertEqual({"dynamic": "deep", "context": "ctx_id", "tracepoint": "tp_id"}, attributes)
