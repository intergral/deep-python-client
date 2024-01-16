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
from typing import List, Optional

from deep.api.tracepoint.constants import SINGLE_FRAME_TYPE, ALL_FRAME_TYPE, NO_FRAME_TYPE, FRAME_TYPE, STACK_TYPE, \
    STACK, FIRE_COUNT, CONDITION


def frame_type_ordinal(frame_type) -> int:
    """
    Convert a frame type to an ordinal (essentially making it an enum). This is useful for ordering.
    :param frame_type: the frame type
    :return: the ordinal of the type
    """
    if frame_type == SINGLE_FRAME_TYPE:
        return 1
    if frame_type == ALL_FRAME_TYPE:
        return 2
    if frame_type == NO_FRAME_TYPE:
        return 0
    # default to single frame if we do not know the type
    return 1


class TracepointWindow:
    """
    This is used to handle validating the time frame for the tracepoint
    """

    def __init__(self, start, end):
        self._start = start
        self._end = end

    def in_window(self, ts):
        """
        Is the provided time in the configured window
        :param ts: time in ms
        :return: true, if the time is within the configured window, else false
        """
        # no window configured - return True
        if self._start == 0 and self._end == 0:
            return True

        # only end configured - return if now is less than end
        if self._start == 0 and self._end > 0:
            return ts <= self._end

        # only start configured - return if now is more than start
        if self._start > 0 and self._end == 0:
            return self._start <= ts

        # if both then check both
        return self._start <= ts <= self._end


class LabelExpression:
    def __init__(self, key: str, static: Optional[any], expression: Optional[str]):
        self.__key = key
        self.__static = static
        self.__expression = expression

    @property
    def key(self):
        return self.__key

    @property
    def static(self):
        return self.__static

    @property
    def expression(self):
        return self.__expression


class MetricDefinition:
    def __init__(self, name: str, labels: list[LabelExpression], type_p: str, expression: Optional[str],
                 namespace: Optional[str], help_p: Optional[str], unit: Optional[str]):
        self.__name = name
        self.__labels = labels
        self.__type = type_p
        self.__expression = expression
        self.__namespace = namespace
        self.__help = help_p
        self.__unit = unit


class TracePointConfig:
    """
    This represents the configuration of a single tracepoint, this is a python version of the GRPC
    data collected from the LongPoll.
    """

    def __init__(self, tp_id: str, path: str, line_no: int, args: dict, watches: List[str],
                 metrics: list[MetricDefinition]):
        self._id = tp_id
        self._path = path
        self._line_no = line_no
        self._args = args
        self._watches = watches

    @property
    def id(self):
        return self._id

    @property
    def path(self):
        return self._path

    @property
    def line_no(self):
        return self._line_no

    @property
    def args(self):
        return self._args

    @property
    def watches(self):
        return self._watches

    @property
    def frame_type(self):
        return self.get_arg(FRAME_TYPE, SINGLE_FRAME_TYPE)

    @property
    def stack_type(self):
        return self.get_arg(STACK_TYPE, STACK)

    @property
    def fire_count(self):
        """
        Get the allowed number of triggers

        :return: the configured number of triggers, or -1 for unlimited triggers
        """
        return self.get_arg_int(FIRE_COUNT, 1)

    @property
    def condition(self):
        return self.get_arg(CONDITION, None)

    def get_arg(self, name: str, default_value: any):
        if name in self._args:
            return self._args[name]
        return default_value

    def get_arg_int(self, name: str, default_value: int):
        try:
            return int(self.get_arg(name, default_value))
        except ValueError:
            return default_value

    def __str__(self) -> str:
        return str({'id': self._id, 'path': self._path, 'line_no': self._line_no, 'args': self._args,
                    'watches': self._watches})

    def __repr__(self) -> str:
        return self.__str__()


class TracepointExecutionStats:
    """
    This keeps track of the tracepoint stats, so we can check fire counts etc
    """

    def __init__(self):
        self._fire_count = 0
        self._last_fire = 0

    def fire(self, ts):
        self._fire_count += 1
        self._last_fire = ts

    @property
    def fire_count(self):
        return self._fire_count

    @property
    def last_fire(self):
        return self._last_fire
