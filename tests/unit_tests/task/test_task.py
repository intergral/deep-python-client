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
from time import sleep

from deep.task import TaskHandler, IllegalStateException


class TestTask(unittest.TestCase):

    def setUp(self):
        self.count = 0

    def task_function(self):
        self.count += 1

    def task_function_sleep(self):
        sleep(2)
        self.count += 1

    def call_back(self, expected):
        return lambda x: self.assertEqual(self.count, expected)

    def test_handle_task(self):
        handler = TaskHandler()
        future = handler.submit_task(self.task_function)
        future.add_done_callback(self.call_back(1))
        handler.flush()

    def test_handle_task_with_error(self):
        def raise_exception():
            raise Exception("test")

        handler = TaskHandler()
        handler.submit_task(raise_exception)
        handler.flush()

    def test_post_flush(self):
        handler = TaskHandler()
        handler.flush()
        self.assertRaises(IllegalStateException, lambda: handler.submit_task(self.task_function))

    def test_flush(self):
        handler = TaskHandler()
        handler.submit_task(self.task_function_sleep)
        handler.submit_task(self.task_function_sleep)
        handler.submit_task(self.task_function_sleep)

        self.assertEqual(self.count, 0)

        handler.flush()

        self.assertEqual(self.count, 3)
