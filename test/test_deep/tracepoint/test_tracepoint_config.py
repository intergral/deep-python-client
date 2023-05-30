#       Copyright (C) 2023  Intergral GmbH
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
