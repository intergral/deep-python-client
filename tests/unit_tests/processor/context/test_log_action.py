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

from parameterized import parameterized

from deep.processor.context.log_action import LogActionContext
from deep.processor.context.trigger_context import TriggerContext
from unit_tests.processor import MockFrame


class TestLogMessages(unittest.TestCase):
    @parameterized.expand([
        ["some log message", "[deep] some log message", {}, []],
        ["some log message: {name}", "[deep] some log message: bob", {'name': 'bob'}, ['bob']],
        ["some log message: {len(name)}", "[deep] some log message: 3", {'name': 'bob'}, ['3']],
        ["some log message: {person}", "[deep] some log message: {'name': 'bob'}",
         {'person': {'name': 'bob'}}, ["Size: 1"]],
        ["some log message: {person.name}", "[deep] some log message: 'dict' object has no attribute 'name'",
         {'person': {'name': 'bob'}}, ["'dict' object has no attribute 'name'"]],
        ["some log message: {person['name']}", "[deep] some log message: bob", {'person': {'name': 'bob'}}, ["bob"]],
    ])
    def test_simple_log_interpolation(self, log_msg, expected_msg, _locals, expected_watches):
        context = LogActionContext(TriggerContext(None, None, MockFrame(_locals), "test"), None)
        log, watches, _vars = context.process_log(log_msg)
        self.assertEqual(expected_msg, log)
        self.assertEqual(len(expected_watches), len(watches))
        for i, watch in enumerate(watches):
            if watch.error is None:
                self.assertEqual(_vars[watch.result.vid].value, expected_watches[i])
            else:
                self.assertEqual(watch.error, expected_watches[i])
