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

"""
Handle events from the python engine to trigger tracepoints.

Using the `sys.settrace` and `threading.settrace` functions we register a function to
process events from the python engine. When we get an event we are interested in (e.g. line) we can match that
to a tracepoint config and if we have a match process the frame data to collect a snapshot, add logs or any
other supported action.
"""

import os
import sys
import threading
from collections import deque
from types import FrameType
from typing import Tuple, TYPE_CHECKING, List, Deque, Optional

from deep import logging
from deep.api.tracepoint.trigger import Trigger
from deep.config import ConfigService
from deep.config.tracepoint_config import ConfigUpdateListener
from deep.processor.context.callback_context import CallbackContext
from deep.processor.context.trigger_context import TriggerContext
from deep.push import PushService
from deep.thread_local import ThreadLocal

if TYPE_CHECKING:
    from deep.processor.context.action_context import ActionContext


class TracepointHandlerUpdateListener(ConfigUpdateListener):
    """This is the listener that connects the config to the handler."""

    def __init__(self, handler):
        """
        Create a new update listener.

        :param handler:  the handler to call when a new tracepoint config is ready
        """
        self._handler = handler

    @staticmethod
    def __add_or_get(target, key, default_value):
        if key not in target:
            target[key] = default_value
        return target[key]

    def config_change(self, ts, old_hash, current_hash, old_config, new_config):
        """
        Process an update to the tracepoint config.

        :param ts: the ts of the new config
        :param old_hash: the old config hash
        :param current_hash: the new config hash
        :param old_config: the old config
        :param new_config: the new config
        """
        self._handler.new_config(new_config)


class TriggerHandler:
    """
    This is the handler for the tracepoints.

    This is where we 'listen' for a hit, and determine if we should collect data.
    """

    def __init__(self, config: ConfigService, push_service: PushService):
        """
        Create a new tigger handler.

        :param config: the config service
        :param push_service: the push service
        """
        self.__old_thread_trace = None
        self.__old_sys_trace = None
        self._push_service = push_service
        self._tp_config: List[Trigger] = []
        self._config = config
        self._config.add_listener(TracepointHandlerUpdateListener(self))
        self._callbacks: ThreadLocal[Deque[CallbackContext]] = ThreadLocal(lambda: deque())

    def start(self):
        """Start the trigger handler."""
        # if we call settrace we cannot use debugger,
        # so we allow the settrace to be disabled, so we can at least debug around it
        if self._config.NO_TRACE:
            return
        self.__old_sys_trace = sys.gettrace()
        # gettrace was added in 3.10, so use it if we can, else try to get from property
        # noinspection PyUnresolvedReferences,PyProtectedMember
        self.__old_thread_trace = threading.gettrace() if hasattr(threading, 'gettrace') else threading._trace_hook
        sys.settrace(self.trace_call)
        threading.settrace(self.trace_call)

    def new_config(self, new_config: List['Trigger']):
        """
        Process a new tracepoint config.

        Called when a change to the tracepoint config is processed.

        :param new_config: the new config to use
        """
        self._tp_config = new_config

    def trace_call(self, frame: FrameType, event: str, arg):
        """
        Process the data for a trace call.

        This is called by the python engine when an event is about to be called.

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
        event, file, line, function = self.location_from_event(event, frame)
        if event in ["line", "return", "exception"] and self._callbacks.is_set:
            self.__process_call_backs(arg, frame, event, file, line, function)

        # return if we do not have any tracepoints
        if len(self._tp_config) == 0:
            return None

        actions = self.__actions_for_location(event, file, line, function, frame)
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

        callbacks = trigger_context.callbacks
        if len(callbacks) > 0:
            logging.debug("Callbacks registered: %s", callbacks)
            self._callbacks.get().append(
                CallbackContext(event, file, line, function, callbacks))

        return self.trace_call

    def __actions_for_location(self, event, file, line, function, frame):
        actions = []
        for trigger in self._tp_config:
            if trigger.at_location(event, file, line, function, frame):
                actions += trigger.actions
        return actions

    def __process_call_backs(self, arg: any, frame: FrameType, event: str, file: str, line: int, function_name: str):
        # remove top context
        context: CallbackContext = self._callbacks.value.pop()
        # if it is for our location process it
        if context.at_location(event, file, line, function_name, frame):
            logging.debug("At callback location %s", context.name)
            context.process(event, frame, arg)
        else:
            logging.debug("Not at callback location %s", context.name)
            # else put the context back on the queue
            self._callbacks.value.append(context)

        if len(self._callbacks.value) == 0:
            logging.debug("Callbacks cleared.")
            self._callbacks.clear()

    @staticmethod
    def location_from_event(event: str, frame: FrameType) -> Tuple[str, str, int, Optional[str]]:
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
        """
        Shutdown this handler.

        Reset the settrace to the previous values.
        """
        sys.settrace(self.__old_sys_trace)
        threading.settrace(self.__old_thread_trace)
