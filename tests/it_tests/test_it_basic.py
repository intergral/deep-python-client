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
import logging
import unittest

import prometheus_client

import deep
import it_tests
from deep.api.tracepoint.constants import LOG_MSG, SNAPSHOT, NO_COLLECT
from it_tests.it_utils import start_server, MockServer
from it_tests.test_target import BPTargetTest
from test_utils import find_var_in_snap_by_name, find_var_in_snap_by_path
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import Metric, MetricType


class BasicITTest(unittest.TestCase):
    """
    These tests are intended to simulate a real user installing and using Deep.

    These tests cannot be debugged as we use the same approach.
    """

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

    def test_log_action(self):
        server: MockServer

        with start_server() as server:
            server.add_tp("test_target.py", 40, {LOG_MSG: 'test log {name}'}, [], [])
            _deep = deep.start(server.config())
            server.await_poll()
            with self.assertLogs('deep', level=logging.INFO) as logs:
                test = BPTargetTest("name", 123)
                _ = test.name
                snapshot = server.await_snapshot()
                _deep.shutdown()

                self.assertIsNotNone(snapshot)

                self.assertEqual("[deep] test log name", snapshot.log_msg)
                self.assertIn("[deep] test log name", logs.output[0])

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

    def test_log_only_action(self):
        """
        For some reason the log message doesn't appear in the output, but it is logged.

        This can be verified by changing the assertion, or looking at the tracepoint handler output.
        """
        server: MockServer

        with start_server() as server:
            server.add_tp("test_target.py", 40, {LOG_MSG: 'test log {name}', SNAPSHOT: NO_COLLECT}, [], [])
            _deep = deep.start(server.config())
            server.await_poll()
            with self.assertLogs('deep', level=logging.INFO) as logs:
                test = BPTargetTest("name", 123)
                _ = test.name
                # we do not want a snapshot, but we have to await to see if one is sent. So we just wait 5 seconds,
                # as it should not take this long for a snapshot to be sent if it was triggered.
                snapshot = server.await_snapshot(timeout=5)

                self.assertIsNone(snapshot)
                self.assertIn("[deep] test log name", logs.output[0])
            _deep.shutdown()

    def test_metric_only_action(self):
        """
        For some reason the log message doesn't appear in the output, but it is logged.

        This can be verified by changing the assertion, or looking at the tracepoint handler output.
        """
        server: MockServer

        with start_server() as server:
            server.add_tp("test_target.py", 40, {SNAPSHOT: NO_COLLECT}, [],
                          [Metric(name="simple_test", type=MetricType.COUNTER)])
            _deep = deep.start(server.config())
            server.await_poll()

            test = BPTargetTest("name", 123)
            _ = test.name
            # we do not want a snapshot, but we have to await to see if one is sent. So we just wait 5 seconds,
            # as it should not take this long for a snapshot to be sent if it was triggered.
            snapshot = server.await_snapshot(timeout=5)

            self.assertIsNone(snapshot)

            self.assertIsNotNone(prometheus_client.REGISTRY._names_to_collectors['deep_simple_test_total'])

            _deep.shutdown()

            with self.assertRaises(KeyError):
                _ = prometheus_client.REGISTRY._names_to_collectors['deep_simple_test_total']
