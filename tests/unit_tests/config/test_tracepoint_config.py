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

from deep.config.tracepoint_config import TracepointConfigService, ConfigUpdateListener
from deep.task import TaskHandler


class TestTracepointConfigService(unittest.TestCase):

    def test_no_change(self):
        service = TracepointConfigService()
        service.update_no_change(1)
        self.assertEqual(1, service._last_update)

        service.update_no_change(2)
        self.assertEqual(2, service._last_update)

    def test_update(self):
        service = TracepointConfigService()
        handler = mockito.mock()
        service.set_task_handler(handler)

        mock_callback = mockito.mock()
        mockito.when(handler).submit_task(mockito.ANY, mockito.eq(1), mockito.eq(None),
                                          mockito.eq("123"), mockito.eq([]),
                                          mockito.eq([])).thenReturn(mock_callback)

        service.update_new_config(1, "123", [])
        self.assertEqual(1, service._last_update)
        self.assertEqual("123", service.current_hash)
        self.assertEqual([], service.current_config)

        mockito.verify(handler, mockito.times(1)).submit_task(mockito.ANY, mockito.eq(1), mockito.eq(None),
                                                              mockito.eq("123"), mockito.eq([]),
                                                              mockito.eq([]))

        mockito.verify(mock_callback, mockito.times(1)).add_done_callback(mockito.ANY)

    def test_update_no_handler(self):
        service = TracepointConfigService()

        service.update_new_config(1, "123", [])
        self.assertEqual(1, service._last_update)
        self.assertEqual("123", service.current_hash)
        self.assertEqual([], service.current_config)

    def test_calls_update_listeners(self):
        service = TracepointConfigService()
        handler = TaskHandler()
        service.set_task_handler(handler)

        self.called = False

        class TestListener(ConfigUpdateListener):

            def config_change(me, ts, old_hash, current_hash, old_config, new_config):
                self.called = True

        service.add_listener(TestListener())

        service.update_new_config(1, "123", [])

        handler.flush()

        self.assertTrue(self.called)

    def test_bad_listener(self):
        service = TracepointConfigService()
        handler = TaskHandler()
        service.set_task_handler(handler)

        self.called = False

        class TestListener(ConfigUpdateListener):

            def config_change(me, ts, old_hash, current_hash, old_config, new_config):
                self.called = True
                raise Exception("test bad listener")

        service.add_listener(TestListener())

        service.add_custom("path", 123, {}, [], [])

        handler.flush()

        self.assertTrue(self.called)

    def test_add_custom_calls_update(self):
        service = TracepointConfigService()
        handler = TaskHandler()
        service.set_task_handler(handler)

        self.called = False

        class TestListener(ConfigUpdateListener):

            def config_change(me, ts, old_hash, current_hash, old_config, new_config):
                self.called = True

        service.add_listener(TestListener())

        service.add_custom("path", 123, {}, [], [])

        handler.flush()

        self.assertTrue(self.called)

    def test_remove_custom_calls_update(self):
        service = TracepointConfigService()
        handler = TaskHandler()
        service.set_task_handler(handler)

        self.called = False

        class TestListener(ConfigUpdateListener):

            def config_change(me, ts, old_hash, current_hash, old_config, new_config):
                self.called = True

        service.add_listener(TestListener())

        custom = service.add_custom("path", 123, {}, [], [])

        handler.flush()

        self.assertTrue(self.called)

        self.called = False

        handler._open = True

        service.remove_custom(custom)

        handler.flush()

        self.assertTrue(self.called)
