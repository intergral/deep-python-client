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
#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

from unittest import TestCase

from parameterized import parameterized

from deep.api.tracepoint.trigger import build_trigger, LineLocation, LocationAction, Trigger, Location


class Test(TestCase):

    @parameterized.expand([
        # Default for line is a snapshot
        ["some.file", 123, {}, [], [],
         Trigger(LineLocation("some.file", 123, Location.Position.START), [
             LocationAction("tp-id", None, {
                 'watches': [],
                 'frame_type': 'single_frame',
                 'stack_type': 'stack',
                 'fire_count': '1',
                 'fire_period': '1000',
                 'log_msg': None,
             }, LocationAction.ActionType.Snapshot)
         ])],
        # create snapshot and log
        ["some.file", 123, {'log_msg': 'some_log'}, [], [],
         Trigger(LineLocation("some.file", 123, Location.Position.START), [
             LocationAction("tp-id", None, {
                 'watches': [],
                 'frame_type': 'single_frame',
                 'stack_type': 'stack',
                 'fire_count': '1',
                 'fire_period': '1000',
                 'log_msg': 'some_log',
             }, LocationAction.ActionType.Snapshot),
         ])],
        # should create all frame snapshot
        ["some.file", 123, {'log_msg': 'some_log', 'frame_type': 'all_frame'}, [], [],
         Trigger(LineLocation("some.file", 123, Location.Position.START), [
             LocationAction("tp-id", None, {
                 'watches': [],
                 'frame_type': 'all_frame',
                 'stack_type': 'stack',
                 'fire_count': '1',
                 'fire_period': '1000',
                 'log_msg': 'some_log',
             }, LocationAction.ActionType.Snapshot),
         ])]
    ])
    def test_build_triggers(self, file, line, args, watches, metrics, expected):
        triggers = build_trigger("tp-id", file, line, args, watches, metrics)
        self.assertEqual(expected, triggers)
