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

import deep.logging
from deep.api.plugin.metric.prometheus_metrics import PrometheusPlugin


class TestPrometheusMetrics(unittest.TestCase):

    def setUp(self):
        deep.logging.init()
        self.plugin = PrometheusPlugin(None)

    def tearDown(self):
        self.plugin.clear()

    def test_counter(self):
        self.plugin.counter("test", {}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_counter_with_labels(self):
        self.plugin.counter("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_duplicate_counter_registration(self):
        self.plugin.counter("test_other", {}, "deep", "", "", 123)
        self.plugin.counter("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_gauge(self):
        self.plugin.gauge("test", {}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_gauge_with_labels(self):
        self.plugin.gauge("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_duplicate_gauge_registration(self):
        self.plugin.gauge("test_other", {}, "deep", "", "", 123)
        self.plugin.gauge("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_histogram(self):
        self.plugin.histogram("test", {}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_histogram_with_labels(self):
        self.plugin.histogram("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_duplicate_histogram_registration(self):
        self.plugin.histogram("test_other", {}, "deep", "", "", 123)
        self.plugin.histogram("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_summary(self):
        self.plugin.summary("test", {}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_summary_with_labels(self):
        self.plugin.summary("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))

    def test_duplicate_summary_registration(self):
        self.plugin.summary("test_other", {}, "deep", "", "", 123)
        self.plugin.summary("test_other", {'value': 'name'}, "deep", "", "", 123)
        self.assertEqual(1, len(self.plugin._cache))
