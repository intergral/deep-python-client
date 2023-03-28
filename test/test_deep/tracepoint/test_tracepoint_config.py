#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
import unittest

from deep.api.tracepoint.tracepoint_config import TracepointWindow, TracePointConfig, FIRE_PERIOD, FIRE_COUNT


class TestTracepointWindow(unittest.TestCase):

    def test_in_window(self):
        window = TracepointWindow(1, 1000)

        self.assertTrue(window.in_window(500))

        self.assertFalse(window.in_window(0))
        self.assertFalse(window.in_window(1001))

    def test_in_window_start(self):
        window = TracepointWindow(1, 0)

        self.assertTrue(window.in_window(500))

        self.assertFalse(window.in_window(0))
        self.assertTrue(window.in_window(1001))

    def test_in_window_end(self):
        window = TracepointWindow(0, 1000)

        self.assertTrue(window.in_window(500))

        self.assertTrue(window.in_window(0))
        self.assertFalse(window.in_window(1001))


class TestTracePointConfig(unittest.TestCase):

    def test_get_arg(self):
        config = TracePointConfig('tp_id', 'path', 123, {'some': 'value'}, [])
        self.assertEqual(config.get_arg('some', 'thing'), 'value')
        self.assertEqual(config.get_arg('other', 'thing'), 'thing')

    def test_get_arg_int(self):
        config = TracePointConfig('tp_id', 'path', 123, {'some': 'value', 'num': 321}, [])
        # noinspection PyTypeChecker
        self.assertEqual(config.get_arg_int('some', 'thing'), 'thing')
        self.assertEqual(config.get_arg_int('other', 123), 123)
        self.assertEqual(config.get_arg_int('num', 123), 321)

    def test_fire_count(self):
        config = TracePointConfig('tp_id', 'path', 123, {'some': 'value', 'num': 321}, [])
        self.assertEqual(config.fire_count, 1)

        self.assertTrue(config.can_trigger(1000))
        config.record_triggered(1000)

        self.assertFalse(config.can_trigger(1001))

    def test_fire_period(self):
        config = TracePointConfig('tp_id', 'path', 123, {FIRE_PERIOD: 10_000, FIRE_COUNT: 10}, [])

        self.assertEqual(config.fire_count, 10)

        self.assertTrue(config.can_trigger(1000))
        config.record_triggered(1000)

        self.assertFalse(config.can_trigger(1001))
