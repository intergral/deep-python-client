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

"""Processing for frame collection."""

import abc
from types import FrameType
from typing import Tuple

from deep.api.tracepoint import StackFrame, Variable
from deep.utils import time_ns
from .variable_set_processor import VariableCacheProvider, VariableSetProcessor, VariableProcessorConfig


class FrameCollectorContext(abc.ABC):

    @property
    @abc.abstractmethod
    def max_tp_process_time(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def collection_config(self) -> VariableProcessorConfig:
        pass

    @property
    @abc.abstractmethod
    def ts(self) -> int:
        pass

    @abc.abstractmethod
    def should_collect_vars(self, frame_index: int) -> bool:
        pass

    @abc.abstractmethod
    def is_app_frame(self, filename: str) -> Tuple[bool, str]:
        pass


class FrameCollector:
    """This deals with collecting data from the paused frames."""
    def __init__(self, source: FrameCollectorContext, frame: FrameType):
        """
        Create a new collector.

        :param frame:  the frame data
        :param config: the deep config service
        """
        self.__has_time_exceeded = False
        self.__source = source
        self.__frame = frame

    def time_exceeded(self) -> bool:
        if self.__has_time_exceeded:
            return self.__has_time_exceeded

        duration = (time_ns() - self.__source.ts) / 1000000  # make duration ms not ns
        self.__has_time_exceeded = duration > self.__source.max_tp_process_time
        return self.__has_time_exceeded

    def parse_short_name(self, filename) -> Tuple[str, bool]:
        is_app_frame, match = self.__source.is_app_frame(filename)
        if match is not None:
            return filename[len(match):], is_app_frame
        return filename, is_app_frame

    def collect(self, var_lookup: dict[str, Variable], var_cache: VariableCacheProvider) \
            -> Tuple[list[StackFrame], dict[str, Variable]]:
        current_frame = self.__frame
        collected_frames = []
        # while we still have frames process them
        while current_frame is not None:
            # process the current frame
            frame = self._process_frame(var_lookup, var_cache, current_frame,
                                        self.__source.should_collect_vars(len(collected_frames)))
            collected_frames.append(frame)
            current_frame = current_frame.f_back
        return collected_frames, var_lookup

    def _process_frame(self, var_lookup: dict[str, Variable], var_cache: VariableCacheProvider,
                       frame: FrameType, collect_vars: bool) -> StackFrame:
        # process the current frame info
        lineno = frame.f_lineno
        filename = frame.f_code.co_filename
        func_name = frame.f_code.co_name

        f_locals = frame.f_locals
        _self = f_locals.get('self', None)
        class_name = None
        if _self is not None and hasattr(_self, '__class__'):
            class_name = _self.__class__.__name__

        var_ids = []
        # only process vars if we are under the time limit
        if collect_vars and not self.time_exceeded():
            processor = VariableSetProcessor(var_lookup, var_cache, self.__source.collection_config)
            # we process the vars as a single dict of 'locals'
            variable, log_str = processor.process_variable("locals", f_locals)
            # now ee 'unwrap' the locals, so they are on the frame directly.
            if variable.vid in var_lookup:
                variable_val = var_lookup[variable.vid]
                del var_lookup[variable.vid]
                var_ids = variable_val.children
        short_path, app_frame = self.parse_short_name(filename)
        return StackFrame(filename, short_path, func_name, lineno, var_ids, class_name,
                          app_frame=app_frame)
