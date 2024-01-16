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

import os
import sys
import threading
from collections import deque
from types import FrameType
from typing import Tuple

from deep import logging
from deep.api.tracepoint.trigger import Trigger
from deep.config import ConfigService
from deep.config.tracepoint_config import ConfigUpdateListener
from deep.processor.context.action_context import ActionContext
from deep.processor.context.action_results import ActionCallback
from deep.processor.context.trigger_context import TriggerContext
from deep.push import PushService
from deep.thread_local import ThreadLocal


class TracepointHandlerUpdateListener(ConfigUpdateListener):
    """
    This is the listener that connects the config to the handler
    """

    def __init__(self, handler):
        self._handler = handler

    def config_change(self, ts, old_hash, current_hash, old_config, new_config):
        self._handler.new_config(new_config)


class TriggerHandler:
    """
    This is the handler for the tracepoints. This is where we 'listen' for a hit, and determine if we
    should collect data.
    """
    _tp_config: list[Trigger]
    __callbacks: ThreadLocal[deque[list[ActionCallback]]] = ThreadLocal(lambda: deque())

    def __init__(self, config: ConfigService, push_service: PushService):
        self.__old_thread_trace = None
        self.__old_sys_trace = None
        self._push_service = push_service
        self._tp_config = []
        self._config = config
        self._config.add_listener(TracepointHandlerUpdateListener(self))

    def start(self):
        # if we call settrace we cannot use debugger,
        # so we allow the settrace to be disabled, so we can at least debug around it
        if self._config.NO_TRACE:
            return
        self.__old_sys_trace = sys.gettrace()
        self.__old_thread_trace = threading.gettrace()
        sys.settrace(self.trace_call)
        threading.settrace(self.trace_call)

    def new_config(self, new_config: list['Trigger']):
        self._tp_config = new_config

    def trace_call(self, frame: FrameType, event: str, arg):
        """
        This is called by python with the current frame data
        The events are as follows:
        - line: a line is being executed
        - call: a function is being called
        - return: a function is being returned
        - exception: an exception is being raised
        :param frame: the current frame
        :param event: the event 'line', 'call', etc. That we are processing.
        :param arg: the args
        :return: None to ignore other calls, or our self to continue
        """
        if event in ["line", "return", "exception"] and self.__callbacks.is_set:
            self.process_call_backs(frame, event)

        # return if we do not have any tracepoints
        if len(self._tp_config) == 0:
            return None

        event, file, line, function = self.location_from_event(event, frame)
        actions = self.actions_for_location(event, file, line, function)
        if len(actions) == 0:
            return self.trace_call

        trigger_context = TriggerContext(self._config, self._push_service, frame, event)
        try:
            with trigger_context:
                for action in actions:
                    try:
                        ctx: ActionContext
                        with trigger_context.action_context(action) as ctx:
                            if ctx.can_trigger():
                                ctx.process()
                    except BaseException:
                        logging.exception("Cannot process action %s", action)
        except BaseException:
            logging.exception("Cannot trigger at %s#%s %s", file, line, function)

        self.__callbacks.get().append(trigger_context.callbacks)

        return self.trace_call

    # def process_tracepoints(self, ts, tracepoints_for, frame):
    #     """
    #     We have some tracepoints, now check if we can collect
    #
    #     :param ts: the nano epoch this trace started
    #     :param tracepoints_for: tracepoints for the file/line
    #     :param frame: the frame data
    #     """
    #     # create a new frame processor with the config
    #     processor = FrameProcessor(ts, tracepoints_for, frame, self._config)
    #     # check if we can collect anything
    #     can_collect = processor.can_collect()
    #     if can_collect:
    #         # we can proceed so have the processor configure from active tracepoints
    #         processor.configure_self()
    #         try:
    #             # collect the data - this can be more than one result
    #             snapshots = processor.collect()
    #             for snapshot in snapshots:
    #                 # push each result to services - this is async to allow the program to resume
    #                 self._push_service.push_snapshot(snapshot)
    #         except Exception:
    #             logging.exception("Failed to collect snapshot")

    def actions_for_location(self, event, file, line, function):
        actions = []
        for trigger in self._tp_config:
            if trigger.at_location(event, file, line, function):
                actions += trigger.actions
        return actions

    def process_call_backs(self, frame: FrameType, event: str):
        callbacks = self.__callbacks.value.pop()
        remaining: list[ActionCallback] = []
        for callback in callbacks:
            if callback.process(frame, event):
                remaining.append(callback)

        self.__callbacks.value.append(remaining)

    @staticmethod
    def location_from_event(event: str, frame: FrameType) -> Tuple[str, str, int, str | None]:
        """
        Convert an event into a location.
        The events are as follows:
            - line: a line is being executed
            - call: a function is being called
            - return: a function is being returned
            - exception: an exception is being raised
        :param event:
        :param frame:
        :returns:
            - event
            - file path
            - line number
            - function name
        """
        filename = os.path.basename(frame.f_code.co_filename)
        line = frame.f_lineno
        function = frame.f_code.co_name
        return event, filename, line, function

    def shutdown(self):
        sys.settrace(self.__old_sys_trace)
        threading.settrace(self.__old_thread_trace)

