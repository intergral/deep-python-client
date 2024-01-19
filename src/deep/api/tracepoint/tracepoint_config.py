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

"""Internal type for configured tracepoints."""

from typing import List, Optional

from deep.api.tracepoint.constants import SINGLE_FRAME_TYPE, ALL_FRAME_TYPE, NO_FRAME_TYPE, FRAME_TYPE, STACK_TYPE, \
    STACK, FIRE_COUNT, CONDITION


def frame_type_ordinal(frame_type) -> int:
    """
    Convert a frame type to an ordinal (essentially making it an enum).

     This is useful for ordering.

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
    """This is used to handle validating the time frame for the tracepoint."""

    def __init__(self, start: int, end: int):
        """
        Create a new tracepoint window.

        :param start: the window start time
        :param end: the window end time
        """
        self._start = start
        self._end = end

    def in_window(self, ts):
        """
        Is the provided time in the configured window.

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
    """A metric label expression."""

    def __init__(self, key: str, static: Optional[any] = None, expression: Optional[str] = None):
        """
        Create a new label expression.

        :param key: the label key
        :param static: the label static value
        :param expression: the label expression
        """
        self.__key = key
        self.__static = static
        self.__expression = expression

    @property
    def key(self):
        """The label key."""
        return self.__key

    @property
    def static(self):
        """The label static value."""
        return self.__static

    @property
    def expression(self):
        """The label expression."""
        return self.__expression

    def __str__(self) -> str:
        """Represent this object as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this object as a string."""
        return self.__str__()

    def __eq__(self, other):
        """Check if other object is equals to this one."""
        if not isinstance(other, LabelExpression):
            return False
        return (
                self.__key == other.__key
                and self.__static == other.__static
                and self.__expression == other.__expression
        )


class MetricDefinition:
    """The definition of a metric to collect."""

    def __init__(self, name: str, metric_type: str, labels: List[LabelExpression] = None,
                 expression: Optional[str] = None,
                 namespace: Optional[str] = None, help_str: Optional[str] = None, unit: Optional[str] = None):
        """
        Create a new metric definition.

        :param name: the metric name
        :param labels: the metric labels
        :param metric_type: the metrics type
        :param expression: the metrics expression
        :param namespace: the metric namespace
        :param help_str: the metric help into
        :param unit: the metric unit
        """
        if labels is None:
            labels = []

        self.name = name
        self.labels = labels
        self.type = metric_type
        self.expression = expression
        self.namespace = namespace
        self.help = help_str
        self.unit = unit

    def __str__(self) -> str:
        """Represent this object as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this object as a string."""
        return self.__str__()

    def __eq__(self, other):
        """Check if other object is equals to this one."""
        if not isinstance(other, MetricDefinition):
            return False
        return (
                self.name == other.name
                and self.labels == other.labels
                and self.type == other.type
                and self.expression == other.expression
                and self.namespace == other.namespace
                and self.help == other.help
                and self.unit == other.unit
        )


class TracePointConfig:
    """
    This represents the configuration of a single tracepoint.

    This is a python version of the GRPC data collected from the LongPoll.
    """

    def __init__(self, tp_id: str, path: str, line_no: int, args: dict, watches: List[str],
                 metrics: List[MetricDefinition]):
        """
        Create a new tracepoint config.

        :param tp_id: the tracepoint id
        :param path: the tracepoint source file
        :param line_no: the tracepoint line number
        :param args: the tracepoint args
        :param watches: the tracepoint watches
        """
        self._id = tp_id
        self._path = path
        self._line_no = line_no
        self._args = args
        self._watches = watches

    @property
    def id(self):
        """The tracepoint id."""
        return self._id

    @property
    def path(self):
        """The tracepoint source file."""
        return self._path

    @property
    def line_no(self):
        """The tracepoint line number."""
        # todo need to support missing line number in grpc
        if self._line_no < 0:
            return 0
        return self._line_no

    @property
    def args(self):
        """The tracepoint args."""
        return self._args

    @property
    def watches(self):
        """The tracepoint watches."""
        return self._watches

    @property
    def frame_type(self):
        """The tracepoint frame type."""
        return self.get_arg(FRAME_TYPE, SINGLE_FRAME_TYPE)

    @property
    def stack_type(self):
        """The tracepoint stack type."""
        return self.get_arg(STACK_TYPE, STACK)

    @property
    def fire_count(self):
        """
        Get the allowed number of triggers.

        :return: the configured number of triggers, or -1 for unlimited triggers
        """
        return self.get_arg_int(FIRE_COUNT, 1)

    @property
    def condition(self):
        """The tracepoint condition."""
        return self.get_arg(CONDITION, None)

    def get_arg(self, name: str, default_value: any):
        """
        Get an arg from tracepoint args.

        :param name: the argument name
        :param default_value: the default value
        :return: the value, or the default value
        """
        if name in self._args:
            return self._args[name]
        return default_value

    def get_arg_int(self, name: str, default_value: int):
        """
        Get an argument from the args as an int.

        :param name: the argument name
        :param default_value: the default value to use.
        :return: the value as an int, or the default value
        """
        try:
            return int(self.get_arg(name, default_value))
        except ValueError:
            return default_value

    def __str__(self) -> str:
        """Represent this object as a string."""
        return str({'id': self._id, 'path': self._path, 'line_no': self._line_no, 'args': self._args,
                    'watches': self._watches})

    def __repr__(self) -> str:
        """Represent this object as a string."""
        return self.__str__()


class TracepointExecutionStats:
    """This keeps track of the tracepoint stats, so we can check fire counts etc."""

    def __init__(self):
        """Create a new stats object."""
        self._fire_count = 0
        self._last_fire = 0

    def fire(self, ts: int):
        """
        Record a fire.

        Call this to record this tracepoint being triggered.

        :param ts: the time in nanoseconds
        """
        self._fire_count += 1
        self._last_fire = ts

    @property
    def fire_count(self):
        """
        The number of times this tracepoint has fired.

        :return: the number of times this has fired.
        """
        return self._fire_count

    @property
    def last_fire(self):
        """
        The time this tracepoint last fired.

        :return: the time in nanoseconds.
        """
        return self._last_fire
