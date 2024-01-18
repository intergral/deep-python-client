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

"""A collection of IT tests that simulate user usage of Deep."""

import unittest

import deep
import it_tests
from it_tests.it_utils import start_server, MockServer
from it_tests.test_target import BPTargetTest
from test_utils import find_var_in_snap_by_name, find_var_in_snap_by_path


class BasicITTest(unittest.TestCase):
    """These tests are intended to simulate a real user installing and using Deep."""

    def test_simple_it(self):
        server: MockServer
        with start_server() as server:
            server.add_tp("test_target.py", 40, {}, [], [])
            _deep = deep.start(server.config({}))
            server.await_poll()
            test = BPTargetTest("name", 123)
            _ = test.name
            snapshot = server.await_snapshot()
            _deep.shutdown()
            self.assertIsNotNone(snapshot)
            frames = snapshot.frames
            self.assertEqual(it_tests.test_target.__file__, frames[0].file_name)
            self.assertEqual("/it_tests/test_target.py", frames[0].short_path)
            self.assertEqual(40, frames[0].line_number)
            self.assertEqual(4, len(frames[0].variables))
            self.assertEqual(6, len(snapshot.var_lookup))

            var_name = find_var_in_snap_by_name(snapshot, "name")
            self.assertIsNotNone(var_name)

            var_i = find_var_in_snap_by_name(snapshot, "i")
            self.assertIsNotNone(var_i)

            var_self = find_var_in_snap_by_name(snapshot, "self")
            self.assertIsNotNone(var_self)

            var_not_on_super = find_var_in_snap_by_path(snapshot, "self._BPSuperClass__not_on_super")
            self.assertIsNotNone(var_not_on_super)
