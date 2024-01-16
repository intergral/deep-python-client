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

import logging
import os
import sys
import threading

from deep.config import ConfigService
from deep.config.tracepoint_config import ConfigUpdateListener
from deep.processor.frame_processor import FrameProcessor
from deep.push import PushService


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
        sorted_config = {}
        for tracepoint in new_config:
            path = os.path.basename(tracepoint.path)
            line_no = tracepoint.line_no
            by_file = self.__add_or_get(sorted_config, path, {})
            by_line = self.__add_or_get(by_file, line_no, [])
            by_line.append(tracepoint)

        self._handler.new_config(sorted_config)


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
        self._push_service = push_service
        self._tp_config = []
        self._config = config
        self._config.add_listener(TracepointHandlerUpdateListener(self))

    def start(self):
        """Start the trigger handler."""
        # if we call settrace we cannot use debugger,
        # so we allow the settrace to be disabled, so we can at least debug around it
        if self._config.NO_TRACE:
            return
        sys.settrace(self.trace_call)
        threading.settrace(self.trace_call)

    def new_config(self, new_config):
        """
        Process a new tracepoint config.

        Called when a change to the tracepoint config is processed.

        :param new_config: the new config to use
        """
        self._tp_config = new_config

    def trace_call(self, frame, event, arg):
        """
        Process the data for a trace call.

        This is called by the python engine when an event is about to be called.

        :param frame: the current frame
        :param event: the event 'line', 'call', etc. That we are processing.
        :param arg: the args
        :return: None to ignore other calls, or our self to continue
        """
        # return if we do not have any tracepoints
        if len(self._tp_config) == 0:
            return None

        tracepoints_for_file, tracepoints_for_line = self.__tracepoints_for(os.path.basename(frame.f_code.co_filename),
                                                                            frame.f_lineno)

        # return if this is not a 'line' event
        if event != 'line':
            if len(tracepoints_for_file) == 0:
                return None
            return self.trace_call

        if len(tracepoints_for_line) > 0:
            self.process_tracepoints(tracepoints_for_line, frame)
        return self.trace_call

    def __tracepoints_for(self, filename, lineno):
        if filename in self._tp_config:
            filename_ = self._tp_config[filename]
            if lineno in filename_:
                return filename_, filename_[lineno]
            return filename_, []
        return [], []

    def process_tracepoints(self, tracepoints_for, frame):
        """
        We have some tracepoints, now check if we can collect.

        :param tracepoints_for: tracepoints for the file/line
        :param frame: the frame data
        """
        # create a new frame processor with the config
        processor = FrameProcessor(tracepoints_for, frame, self._config)
        # check if we can collect anything
        can_collect = processor.can_collect()
        if can_collect:
            # we can proceed so have the processor configure from active tracepoints
            processor.configure_self()
            try:
                # collect the data - this can be more than one result
                snapshots = processor.collect()
                for snapshot in snapshots:
                    # push each result to services - this is async to allow the program to resume
                    self._push_service.push_snapshot(snapshot)
            except Exception:
                logging.exception("Failed to collect snapshot")
