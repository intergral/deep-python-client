#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from deep.api.tracepoint.tracepoint_config import SINGLE_FRAME_TYPE, STACK, \
    frame_type_ordinal, STACK_TYPE, FRAME_TYPE, \
    TracePointConfig, NO_FRAME_TYPE, ALL_FRAME_TYPE


class FrameProcessorConfig:
    """
    This is the config for a data collection.
    """
    DEFAULT_MAX_VAR_DEPTH = 5
    DEFAULT_MAX_VARIABLES = 1000
    DEFAULT_MAX_COLLECTION_SIZE = 10
    DEFAULT_MAX_STRING_LENGTH = 1024
    DEFAULT_MAX_WATCH_VARS = 100
    DEFAULT_MAX_TP_PROCESS_TIME = 100
    DEFAULT_MAX_PROFILE_TIME = 1000
    DEFAULT_PROFILE_INTERVAL = 10

    def __init__(self):
        self._frame_type = None
        self._stack_type = None
        self._max_var_depth = -1
        self._max_variables = -1
        self._max_collection_size = -1
        self._max_string_length = -1
        self._max_watch_vars = -1
        self._max_tp_process_time = -1

    def process_tracepoint(self, tp: TracePointConfig):
        """
        Each tracepoint can have a different  config we want to re-configure to the lowest impact. e.g. if all
        tracepoints are single frame, then do not collect all frames.
        :param tp: the tracepoint to process
        """
        self._max_var_depth = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_VAR_DEPTH', self._max_var_depth)
        self._max_variables = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_VARIABLES', self._max_variables)
        self._max_collection_size = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_COLLECTION_SIZE',
                                                                            self._max_collection_size)
        self._max_string_length = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_STRING_LENGTH',
                                                                          self._max_string_length)
        self._max_watch_vars = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_WATCH_VARS', self._max_watch_vars)
        self._max_tp_process_time = FrameProcessorConfig.get_max_or_default(tp.args, 'MAX_TP_PROCESS_TIME',
                                                                            self._max_tp_process_time)

        # use the highest collection type - results can be trimmed during pre upload processing
        frame_type = tp.get_arg(FRAME_TYPE, None)
        if frame_type is not None:
            if self._frame_type is None:
                self._frame_type = frame_type
            elif frame_type_ordinal(frame_type) > frame_type_ordinal(self._frame_type):
                self._frame_type = frame_type

        # collect stack if any require it
        stack_type = tp.get_arg(STACK_TYPE, None)
        if stack_type is not None:
            if self._stack_type is None:
                self._stack_type = stack_type
            elif stack_type == STACK:
                self._stack_type = STACK

    def close(self):
        """Close the config, to check for any unconfirmed parts, and set them to defaults."""

        # todo: What if one tp has 'MAX_VARS' as 10, but others do not have it set.

        self._max_var_depth = FrameProcessorConfig.DEFAULT_MAX_VAR_DEPTH if self._max_var_depth == -1 \
            else self._max_var_depth
        self._max_variables = FrameProcessorConfig.DEFAULT_MAX_VARIABLES if self._max_variables == -1 \
            else self._max_variables
        self._max_collection_size = FrameProcessorConfig.DEFAULT_MAX_COLLECTION_SIZE \
            if self._max_collection_size == -1 \
            else self._max_collection_size
        self._max_string_length = FrameProcessorConfig.DEFAULT_MAX_STRING_LENGTH if self._max_string_length == -1 \
            else self._max_string_length
        self._max_watch_vars = FrameProcessorConfig.DEFAULT_MAX_WATCH_VARS if self._max_watch_vars == -1 \
            else self._max_watch_vars
        self._max_tp_process_time = FrameProcessorConfig.DEFAULT_MAX_TP_PROCESS_TIME \
            if self._max_tp_process_time == -1 \
            else self._max_tp_process_time

        if self._frame_type is None:
            self._frame_type = SINGLE_FRAME_TYPE

        if self._stack_type is None:
            self._stack_type = STACK

    @staticmethod
    def get_max_or_default(config, key, default_value):
        if key in config:
            return max(int(config[key]), default_value)
        return default_value

    @property
    def frame_type(self):
        return self._frame_type

    @property
    def stack_type(self):
        return self._stack_type

    @property
    def max_var_depth(self):
        return self._max_var_depth

    @property
    def max_variables(self):
        return self._max_variables

    @property
    def max_collection_size(self):
        return self._max_collection_size

    @property
    def max_string_length(self):
        return self._max_string_length

    @property
    def max_watch_vars(self):
        return self._max_watch_vars

    @property
    def max_tp_process_time(self):
        return self._max_tp_process_time

    def should_collect_vars(self, current_frame_index):
        if self._frame_type == NO_FRAME_TYPE:
            return False
        if current_frame_index == 0:
            return True
        elif self._frame_type == ALL_FRAME_TYPE:
            return True
        return False
