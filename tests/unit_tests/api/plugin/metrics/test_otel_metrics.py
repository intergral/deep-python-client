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

from mockito import when, mock, verify
from opentelemetry.metrics import set_meter_provider, MeterProvider

import deep.logging
from deep.api.plugin.metric.otel_metrics import OTelMetrics


class TestOtelMetrics(unittest.TestCase):
    mock_provider = mock(MeterProvider)

    @classmethod
    def setUpClass(cls):
        deep.logging.init()

        set_meter_provider(cls.mock_provider)

    def setUp(self):
        self.deep_provider = mock()
        when(self.mock_provider).get_meter('deep', '').thenReturn(self.deep_provider)
        when(self.mock_provider).get_meter('deep', '', None).thenReturn(self.deep_provider)

    def test_post_counter_twice(self):
        metric = mock()
        when(self.deep_provider).create_counter('test_counter', "unit", "help").thenReturn(metric)
        metrics = OTelMetrics(None)
        metrics.counter("counter", {}, "test", "help", "unit", 1)
        metrics.counter("counter", {}, "test", "help", "unit", 1)

        verify(self.deep_provider, 1).create_counter('test_counter', "unit", "help")
        verify(metric, 2).add(1, {})

    def test_post_counter(self):
        metric = mock()
        when(self.deep_provider).create_counter('test_counter', "unit", "help").thenReturn(metric)
        metrics = OTelMetrics(None)
        metrics.counter("counter", {}, "test", "help", "unit", 1)

        verify(self.deep_provider, 1).create_counter('test_counter', "unit", "help")

        verify(metric).add(1, {})

    def test_post_histogram(self):
        metric = mock()
        when(self.deep_provider).create_histogram('test_histogram', "unit", "help").thenReturn(metric)
        metrics = OTelMetrics(None)
        metrics.histogram("histogram", {}, "test", "help", "unit", 1)

        verify(metric).record(1, {})

    def test_post_gauge(self):
        metric = mock()
        when(self.deep_provider).create_up_down_counter('test_gauge', "unit", "help").thenReturn(metric)
        metrics = OTelMetrics(None)
        metrics.gauge("gauge", {}, "test", "help", "unit", 1)

        verify(metric).add(1, {})

    def test_post_summary(self):
        metric = mock()
        when(self.deep_provider).create_histogram('test_summary', "unit", "help").thenReturn(metric)
        metrics = OTelMetrics(None)
        metrics.summary("summary", {}, "test", "help", "unit", 1)

        verify(metric).record(1, {})

    def test_post_counter_error(self):
        metric = mock()
        when(self.deep_provider).create_counter('test_counter', "unit", "help").thenRaise(Exception("test otel error"))
        metrics = OTelMetrics(None)
        metrics.counter("counter", {}, "test", "help", "unit", 1)

        verify(self.deep_provider, 1).create_counter('test_counter', "unit", "help")

        verify(metric, 0).add(1, {})

    def test_post_histogram_error(self):
        metric = mock()
        when(self.deep_provider).create_histogram('test_histogram', "unit", "help").thenRaise(
            Exception("test otel error"))
        metrics = OTelMetrics(None)
        metrics.histogram("histogram", {}, "test", "help", "unit", 1)

        verify(metric, 0).record(1, {})

    def test_post_gauge_error(self):
        metric = mock()
        when(self.deep_provider).create_up_down_counter('test_gauge', "unit", "help").thenRaise(
            Exception("test otel error"))
        metrics = OTelMetrics(None)
        metrics.gauge("gauge", {}, "test", "help", "unit", 1)

        verify(metric, 0).add(1, {})

    def test_post_summary_error(self):
        metric = mock()
        when(self.deep_provider).create_histogram('test_summary', "unit", "help").thenRaise(
            Exception("test otel error"))
        metrics = OTelMetrics(None)
        metrics.summary("summary", {}, "test", "help", "unit", 1)

        verify(metric, 0).record(1, {})
