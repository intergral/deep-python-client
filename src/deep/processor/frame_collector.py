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
from typing import Tuple, Dict, List

from deep.api.tracepoint import StackFrame, Variable
from deep.utils import time_ns
from .variable_set_processor import VariableCacheProvider, VariableSetProcessor, VariableProcessorConfig


class FrameCollectorContext(abc.ABC):
    """The context that is used to wrap a collection event."""

    @property
    @abc.abstractmethod
    def max_tp_process_time(self) -> int:
        """The max time to spend processing a tracepoint."""
        pass

    @property
    @abc.abstractmethod
    def collection_config(self) -> VariableProcessorConfig:
        """The variable processing config."""
        pass

    @property
    @abc.abstractmethod
    def ts(self) -> int:
        """The timestamp in nanoseconds for this trigger."""
        pass

    @abc.abstractmethod
    def should_collect_vars(self, current_frame_index: int) -> bool:
        """
        Check if we can collect data for a frame.

        Frame indexes start from 0 (as the current frame) and increase as we go back up the stack.

        :param (int) current_frame_index: the current frame index.
        :return (bool): if we should collect the frame vars.
        """
        pass

    @abc.abstractmethod
    def is_app_frame(self, filename: str) -> Tuple[bool, str]:
        """
        Check if the current frame is a user application frame.

        :param filename: the frame file name
        :return: True if add frame, else False
        """
        pass


class FrameCollector:
    """This deals with collecting data from the paused frames."""

    def __init__(self, source: FrameCollectorContext, frame: FrameType):
        """
        Create a new collector.

        :param source: the collector context
        :param frame:  the frame data
        """
        self.__has_time_exceeded = False
        self.__source = source
        self.__frame = frame

    def __time_exceeded(self) -> bool:
        if self.__has_time_exceeded:
            return self.__has_time_exceeded

        duration = (time_ns() - self.__source.ts) / 1000000  # make duration ms not ns
        self.__has_time_exceeded = duration > self.__source.max_tp_process_time
        return self.__has_time_exceeded

    def parse_short_name(self, filename) -> Tuple[str, bool]:
        """
        Process a file name into a shorter version.

        By default, the file names in python are the absolute path to the file on disk. These can be quite long,
        so we try to shorten the names by looking at the APP_ROOT and converting the file name into a relative path.

        e.g. if the file name is '/dev/python/custom_service/api/handler.py' and the APP_ROOT is
            '/dev/python/custom_service' then we shorten the path to 'custom_service/api/handler.py'.

        :param (str) filename: the file name
        :returns:
            (str) filename: the new file name
            (bool) is_app_frame: True if the file is an application frame file
        """
        is_app_frame, match = self.__source.is_app_frame(filename)
        if match is not None:
            return filename[len(match):], is_app_frame
        return filename, is_app_frame

    def collect(self, var_lookup: Dict[str, Variable], var_cache: VariableCacheProvider) \
            -> Tuple[List[StackFrame], Dict[str, Variable]]:
        """
        Collect the data from the current frame.

        :param var_lookup: the var lookup to use
        :param var_cache: the var cache to use
        :return:
        """
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

    def _process_frame(self, var_lookup: Dict[str, Variable], var_cache: VariableCacheProvider,
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
        if collect_vars and not self.__time_exceeded():
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
