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

import threading
import unittest
from threading import Thread

from deep import logging
from deep.api.resource import Resource
from deep.api.tracepoint.constants import LOG_MSG, WATCHES
from deep.api.tracepoint.eventsnapshot import EventSnapshot

from deep.api.tracepoint.trigger import Location, LocationAction, LineLocation, Trigger
from deep.config import ConfigService
from deep.logging.tracepoint_logger import TracepointLogger
from deep.processor.trigger_handler import TriggerHandler
from deep.push.push_service import PushService
from deep_tests.test_target import some_test_function


class MockPushService(PushService):
    def __init__(self, config, grpc, task_handler):
        super().__init__(config, grpc, task_handler)
        self.pushed: list[EventSnapshot] = []

    def push_snapshot(self, snapshot: EventSnapshot):
        self.pushed.append(snapshot)


class MockTracepointLogger(TracepointLogger):

    def __init__(self):
        self.logged = []

    def log_tracepoint(self, log_msg: str, tp_id: str, ctx_id: str):
        self.logged.append(log_msg)


class MockConfigService(ConfigService):
    def __init__(self, custom):
        super().__init__(custom)
        self.logger = MockTracepointLogger()

    @property
    def tracepoint_logger(self) -> 'TracepointLogger':
        return self.logger

    @property
    def resource(self) -> Resource:
        return Resource.get_empty()


class TraceCallCapture:

    def __init__(self):
        self.captured_frame = None
        self.captured_event = None
        self.captured_args = None

    def capture_trace_call(self, location: Location):
        def trace_call(frame, event, args):
            event, file, line, function = TriggerHandler.location_from_event(event, frame)
            if location.at_location(event, file, line, function):
                self.captured_frame = frame
                self.captured_event = event
                self.captured_args = args
            return trace_call

        return trace_call


logging.init(MockConfigService({}))


class TestTriggerHandler(unittest.TestCase):

    def call_and_capture(self, location, func, args, capture):
        # here we execute the real code using a mock trace call that will capture the args to trace call
        # we cannot debug this section of the code
        current = threading.gettrace()
        threading.settrace(capture.capture_trace_call(location))
        thread = Thread(target=func, args=args)
        thread.start()
        thread.join(10)
        threading.settrace(current)
        # now we call our real version of the trace_call with the captured data
        # we can now debug the code we cannot normally debug

        if capture.captured_frame is None:
            self.fail("Did not capture")

    def test_log_action(self):
        capture = TraceCallCapture()
        config = MockConfigService({})
        push = MockPushService(None, None, None)
        handler = TriggerHandler(config, push)

        location = LineLocation('test_target.py', 19, Location.Position.START)
        handler.new_config(
            [Trigger(location, [LocationAction("tp_id", None, {LOG_MSG: "some log"}, LocationAction.ActionType.Log)])])

        self.call_and_capture(location, some_test_function, ['args'], capture)

        handler.trace_call(capture.captured_frame, capture.captured_event, capture.captured_args)

        logged = config.logger.logged
        self.assertEqual(1, len(logged))
        self.assertEqual("[deep] some log", logged[0])

    def test_log_action_with_watch(self):
        capture = TraceCallCapture()
        config = MockConfigService({})
        push = MockPushService(None, None, None)
        handler = TriggerHandler(config, push)

        location = LineLocation('test_target.py', 19, Location.Position.START)
        handler.new_config([Trigger(location, [
            LocationAction("tp_id", None, {LOG_MSG: "some log {val}"}, LocationAction.ActionType.Log)])])

        self.call_and_capture(location, some_test_function, ['input'], capture)

        handler.trace_call(capture.captured_frame, capture.captured_event, capture.captured_args)

        logged = config.logger.logged
        self.assertEqual(1, len(logged))
        self.assertEqual("[deep] some log inputsomething", logged[0])

    def test_snapshot_action(self):
        capture = TraceCallCapture()
        config = MockConfigService({})
        push = MockPushService(None, None, None)
        handler = TriggerHandler(config, push)

        location = LineLocation('test_target.py', 19, Location.Position.START)
        handler.new_config([Trigger(location, [
            LocationAction("tp_id", None, {WATCHES: ['arg']}, LocationAction.ActionType.Snapshot)])])

        self.call_and_capture(location, some_test_function, ['input'], capture)

        handler.trace_call(capture.captured_frame, capture.captured_event, capture.captured_args)

        logged = config.logger.logged
        self.assertEqual(0, len(logged))
        pushed = push.pushed
        self.assertEqual(1, len(pushed))
        self.assertEqual(2, len(pushed[0].var_lookup))
        self.assertEqual(2, len(pushed[0].frames[0].variables))

        self.assertEqual(1, len(pushed[0].watches))
        self.assertEqual("arg", pushed[0].watches[0].expression)
        self.assertEqual("arg", pushed[0].watches[0].result.name)
        self.assertEqual("input", pushed[0].var_lookup[pushed[0].watches[0].result.vid].value)

    def test_snapshot_action_with_condition(self):
        capture = TraceCallCapture()
        config = MockConfigService({})
        push = MockPushService(None, None, None)
        handler = TriggerHandler(config, push)

        location = LineLocation('test_target.py', 19, Location.Position.START)
        handler.new_config([Trigger(location, [
            LocationAction("tp_id", "arg == None", {}, LocationAction.ActionType.Snapshot)])])

        self.call_and_capture(location, some_test_function, ['input'], capture)

        handler.trace_call(capture.captured_frame, capture.captured_event, capture.captured_args)

        logged = config.logger.logged
        self.assertEqual(0, len(logged))
        pushed = push.pushed
        self.assertEqual(0, len(pushed))
