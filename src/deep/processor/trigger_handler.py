import logging
import os
import sys
import threading

from deep.config.tracepoint_config import ConfigUpdateListener
from deep.processor.frame_processor import FrameProcessor


def add_or_get(target, key, default_value):
    if key not in target:
        target[key] = default_value
    return target[key]


class TracepointHandlerUpdateListener(ConfigUpdateListener):
    def __init__(self, handler):
        self._handler = handler

    def config_change(self, ts, old_hash, current_hash, old_config, new_config):
        sorted_config = {}
        for tracepoint in new_config:
            path = os.path.basename(tracepoint.path)
            line_no = tracepoint.line_no
            by_file = add_or_get(sorted_config, path, {})
            by_line = add_or_get(by_file, line_no, [])
            by_line.append(tracepoint)

        self._handler.new_config(sorted_config)


class TriggerHandler:
    def __init__(self, config, push_service):
        self._push_service = push_service
        self._tp_config = []
        self._config = config
        self._config.add_listener(TracepointHandlerUpdateListener(self))

    def start(self):
        sys.settrace(self.trace_call)
        threading.settrace(self.trace_call)

    def new_config(self, new_config):
        self._tp_config = new_config

    def trace_call(self, frame, event, arg):

        # return if we do not have any tracepoints
        if len(self._tp_config) == 0:
            return None

        tracepoints_for_file, tracepoints_for_line = self.tracepoints_for(os.path.basename(frame.f_code.co_filename),
                                                                          frame.f_lineno)

        # return if this is not a 'line' event
        if event != 'line':
            if len(tracepoints_for_file) == 0:
                return None
            return self.trace_call

        if len(tracepoints_for_line) > 0:
            self.process_tracepoints(tracepoints_for_line, frame, event, arg)
        return self.trace_call

    def tracepoints_for(self, filename, lineno):
        if filename in self._tp_config:
            filename_ = self._tp_config[filename]
            if lineno in filename_:
                return filename_, filename_[lineno]
            return filename_, []
        return [], []

    def process_tracepoints(self, tracepoints_for, frame, event, arg):
        processor = FrameProcessor(tracepoints_for, frame, self._config)
        can_collect = processor.can_collect()
        if can_collect:
            processor.configure_self()
            try:
                snapshots = processor.collect()
                for snapshot in snapshots:
                    self._push_service.push_snapshot(snapshot)
            except:
                logging.exception("Failed to collect snapshot")
