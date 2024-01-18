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
        self.plugin = PrometheusPlugin()

    def tearDown(self):
        self.plugin.clear()

    def test_counter(self):
        self.plugin.counter("test", {}, "deep", "", "", 123)

    def test_counter_with_labels(self):
        self.plugin.counter("test_other", {'value': 'name'}, "deep", "", "", 123)

    def test_duplicate_registration(self):
        self.plugin.counter("test_other", {}, "deep", "", "", 123)
        self.plugin.counter("test_other", {'value': 'name'}, "deep", "", "", 123)
