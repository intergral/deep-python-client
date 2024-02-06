#       Copyright (C) 2024  Intergral GmbH
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

"""Handlers for triggers and action configs."""

import abc
import inspect
from enum import Enum
from types import FrameType

from typing import Optional, Dict, List

from deep.api.tracepoint.constants import WINDOW_START, WINDOW_END, FIRE_COUNT, FIRE_PERIOD, LOG_MSG, WATCHES, \
    LINE_START, METHOD_START, METHOD_END, LINE_END, LINE_CAPTURE, METHOD_CAPTURE, NO_COLLECT, SNAPSHOT, CONDITION, \
    FRAME_TYPE, STACK_TYPE, SINGLE_FRAME_TYPE, STACK, SPAN, STAGE, METHOD_NAME, LINE_STAGES, METHOD_STAGES, METHOD
from deep.api.tracepoint.tracepoint_config import TracepointWindow, TracepointExecutionStats, MetricDefinition, \
    TracePointConfig


class LocationAction(object):
    """
    This defines an action to perform. This action can be any action that is configured via a tracepoint.

    Supported actions are:
     - snapshot: collect local variable data and stack frames at location
     - log: evaluate a log message at the location
     - metric: evaluate a metric and process via provider
     - span: create a span at this location
    """

    class ActionType(Enum):
        """The type of action."""

        Snapshot = 1
        Log = 2
        Metric = 3
        Span = 4

        def __str__(self):
            """Represent this as a string."""
            return self.name

        def __repr__(self):
            """Represent this as a string."""
            return self.name

    def __init__(self, tp_id: str, condition: Optional[str], config: Dict[str, any], action_type: ActionType):
        """
        Create a new location action.

        :param tp_id: the tracepoint id
        :param condition: the condition
        :param config: the config
        :param action_type: the action type
        """
        self.__id = tp_id
        self.__condition = condition
        self.__config = config
        self.__window = TracepointWindow(self.__config.get(WINDOW_START, 0), self.__config.get(WINDOW_END, 0))
        self.__stats = TracepointExecutionStats()
        self.__action_type = action_type
        self.__location: Optional['Location'] = None

    @property
    def id(self) -> str:
        """
        The id of the tracepoint that created this action.

        :return: the tracepoint id
        """
        return self.__id

    @property
    def condition(self) -> Optional[str]:
        """
        The condition that is set on the tracepoint.

        :return: the condition if set
        """
        return self.__condition

    @property
    def config(self) -> Dict[str, any]:
        """
        The config for this action.

        :return: the full action config.
        """
        return self.__config

    @property
    def fire_count(self):
        """
        Get the allowed number of triggers.

        :return: the configured number of triggers, or -1 for unlimited triggers
        """
        return self.__get_int(FIRE_COUNT, 1)

    @property
    def fire_period(self):
        """
        Get the minimum amount of time that has to have elapsed before this can trigger again.

        :return: the time in ms
        """
        return self.__get_int(FIRE_PERIOD, 1000)

    @property
    def action_type(self) -> ActionType:
        """Get the action type."""
        return self.__action_type

    @property
    def location(self) -> Optional['Location']:
        """Get the location config."""
        return self.__location

    @property
    def tracepoint(self) -> TracePointConfig:
        """Get the tracepoint config for this trigger."""
        args = dict(self.__config)
        if WATCHES in args:
            del args[WATCHES]
        if LOG_MSG in args and args[LOG_MSG] is None:
            del args[LOG_MSG]
        return TracePointConfig(self.id, self.__location.path, self.__location.line, args,
                                self.__config.get(WATCHES, []), [])

    def __fire_period_ns(self):
        return self.fire_period * 1_000_000

    def can_trigger(self, ts):
        """
        Check if the tracepoint can trigger.

        This is to check the config. e.g. fire count, fire windows etc.
        :param ts: the time the tracepoint has been triggered
        :return: true, if we should collect data; else false
        """
        # Have we exceeded the fire count?
        if self.fire_count != -1 and self.fire_count <= self.__stats.fire_count:
            return False

        # Are we in the time window?
        if not self.__window.in_window(ts):
            return False

        # Have we fired too quickly?
        last_fire = self.__stats.last_fire
        if last_fire != 0:
            time_since_last = ts - last_fire
            if time_since_last < self.__fire_period_ns():
                return False

        return True

    def record_triggered(self, ts):
        """
        Record a fire.

        Call this to record this tracepoint being triggered.

        :param ts: the time in nanoseconds
        """
        self.__stats.fire(ts)

    def __get_int(self, name: str, default_value: int):
        try:
            return int(self.__config.get(name, default_value))
        except ValueError:
            return default_value

    def __str__(self):
        """Represent this as a string."""
        return str({
            'id': self.__id,
            'condition': self.__condition,
            'config': self.__config,
            'type': self.__action_type
        })

    def __repr__(self):
        """Represent this as a string."""
        return self.__str__()

    def __eq__(self, __value):
        """Check if this is equal to another."""
        if self.__id == __value.__id and self.__condition == __value.__condition and self.__config == __value.__config:
            return True
        return False

    def with_location(self, location: 'Location') -> 'LocationAction':
        """
        Attach the location to this action.

        It is sometimes required to get the location information from an action. So we attach them here.

        :param location: the location we are attached to.
        :return: self
        """
        self.__location = location
        return self


class Location(abc.ABC):
    """A location is the line or method at which actions should be performed."""

    class Position(Enum):
        """Position lets the location be at the start, end or capture."""

        START = 1
        END = 2
        CAPTURE = 3

        @classmethod
        def from_stage(cls, stage_: str):
            """
            Get the stage enum from a string.

            :param (str) stage_: the input string
            :return: the appropriate stage enum
            """
            if stage_ in [LINE_START, METHOD_START]:
                return Location.Position.START
            if stage_ in [LINE_END, METHOD_END]:
                return Location.Position.END
            if stage_ in [LINE_CAPTURE, METHOD_CAPTURE]:
                return Location.Position.CAPTURE
            return Location.Position.START

    def __init__(self, position: Position = None):
        """
        Create a new location.

        :param position: the position of this location
        """
        self.position = position

    @abc.abstractmethod
    def at_location(self, event: str, file: str, line: int, function_name: str, frame: FrameType) -> bool:
        """
        Check if we are at the location defined by this location.

        :param event: the trigger event
        :param file: the file path
        :param line: the line number
        :param function_name: the function name
        :param frame: the triggering frame object
        :return: True, if we are at this location we expect, else False.
        """
        pass

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """The location id."""
        pass

    @property
    @abc.abstractmethod
    def path(self) -> str:
        """The source file path."""
        pass

    @property
    @abc.abstractmethod
    def line(self) -> int:
        """The line number."""
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        The name for this location.

        For Method locations should be method name.
        For line location should be the file#line number.
        """
        pass


class Trigger(Location):
    """
    A trigger is a location with actions.

    A trigger describes the location at which deep should take some actions.

    A location is the combination of the file, line, function name, and position. Combining these we can add
    actions at the start or end of lines, or functions.
    """

    def __init__(self, location: Location, actions: List[LocationAction]):
        """
        Create new trigger.

        :param location: the location
        :param actions: the actions
        """
        super().__init__()
        self.__location = location
        self.__actions = actions

    def at_location(self, event: str, file: str, line: int, function_name: str, frame: FrameType) -> bool:
        """
        Check if we are at the location defined by this location.

        :param event: the trigger event
        :param file: the file path
        :param line: the line number
        :param function_name: the method name
        :param frame: the triggering frame object
        :return: True, if we are at this location we expect, else False.
        """
        return self.__location.at_location(event, file, line, function_name, frame)

    @property
    def actions(self) -> List[LocationAction]:
        """The actions that are attached to this location."""
        return [action.with_location(self) for action in self.__actions]

    @property
    def id(self):
        """The location id."""
        return self.__location.id

    @property
    def path(self):
        """The source file path."""
        return self.__location.path

    @property
    def line(self):
        """The line number."""
        return self.__location.line

    @property
    def name(self) -> str:
        """
        The name for this location.

        For Method locations should be method name.
        For line location should be the file#line number.
        """
        return self.__location.name

    def __str__(self):
        """Represent this as a string."""
        return str({
            'location': self.__location,
            'actions': self.__actions
        })

    def __repr__(self):
        """Represent this as a string."""
        return self.__str__()

    def __eq__(self, __value):
        """Check if this is equal to another."""
        if self.__location == __value.__location and self.__actions == __value.__actions:
            return True
        return False

    def merge_actions(self, actions: List[LocationAction]):
        """Merge more actions into this location."""
        self.__actions += actions


class LineLocation(Location):
    """A location for a line entry/exit/capture point."""

    def __init__(self, path: str, line: int, position: Location.Position):
        """
        Create new line location.

        :param path:  the source file path
        :param line: the line number
        :param position: the position
        """
        super().__init__(position)
        self.__path = path
        self.__line = line

    def at_location(self, event: str, file: str, line: int, function_name: str, frame: FrameType):
        """
        Check if we are at the location defined by this location.

        Line actions must always trigger on the line they define. So we do not look at the position here.

        :param event: the trigger event
        :param file: the file path
        :param line: the line number
        :param function_name: the method name
        :param frame: the triggering frame object
        :return: True, if we are at this location we expect, else False.
        """
        if event == "line" and file == self.path and line == self.line:
            return True
        return False

    @property
    def id(self):
        """The location id."""
        return "%s#%s" % (self.path, self.line)

    @property
    def path(self):
        """The source file path."""
        return self.__path

    @property
    def line(self):
        """The line number."""
        return self.__line

    @property
    def name(self) -> str:
        """
        The name for this location.

        For line location should be the file#line number.
        """
        return f'{self.path}#{self.line}'

    def __str__(self):
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self):
        """Represent this as a string."""
        return self.__str__()

    def __eq__(self, __value):
        """Check if this is equal to another."""
        if self.path == __value.path and self.line == __value.line:
            return True
        return False


class FunctionLocation(Location):
    """A location for a method entry/exit/capture point."""

    def __init__(self, path: str, function_name: Optional[str], position: Location.Position):
        """
        Create a new method location.

        :param path:  the source file path
        :param function_name: the function name
        :param position: the position
        """
        super().__init__(position)
        self.__function_name = function_name
        self.__path = path

    def at_location(self, event: str, file: str, line: int, function_name: str, frame: FrameType):
        """
        Check if we are at the location defined by this location.

        :param event: the trigger event
        :param file: the file path
        :param line: the line number
        :param function_name: the method name
        :param frame: the triggering frame object
        :return: True, if we are at this location we expect, else False.
        """
        if file != self.path:
            return False

        # if method_name is not set then we need to discover it from the frame.
        if self.__function_name is None:
            # load source lines
            lines, start = inspect.getsourcelines(frame)
            end = start + len(lines)
            # if the targeted line is in the range of start to end
            if start <= line >= end:
                # set the method to this name (so we do not need to look it up again)
                self.__function_name = function_name
                return True
            return False

        if event == "call" and function_name == self.__function_name:
            return True
        return False

    @property
    def id(self):
        """The location id."""
        return "%s#%s" % (self.path, self.__function_name)

    @property
    def path(self):
        """The source file path."""
        return self.__path

    @property
    def line(self):
        """The method location always has a line of -1."""
        return -1

    @property
    def name(self) -> str:
        """
        The name for this location.

        For Method locations should be method name.
        """
        return self.__function_name

    def __str__(self):
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self):
        """Represent this as a string."""
        return self.__str__()

    def __eq__(self, __value):
        """Check if this is equal to another."""
        if self.path == __value.path and self.__function_name == __value.__function_name:
            return True
        return False


def build_snapshot_action(tp_id: str, args: Dict[str, str], watches: List[str]) -> Optional[LocationAction]:
    """
    Create an action to create a snapshot.

    :param tp_id: the tracepoint id
    :param args: the args
    :param watches: the watch expressions
    :return: the location action
    """
    if SNAPSHOT in args:
        if args[SNAPSHOT] == NO_COLLECT:
            return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        WATCHES: watches,
        FRAME_TYPE: args.get(FRAME_TYPE, SINGLE_FRAME_TYPE),
        STACK_TYPE: args.get(STACK_TYPE, STACK),
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
        LOG_MSG: args.get(LOG_MSG, None),
    }, LocationAction.ActionType.Snapshot)


def build_log_action(tp_id: str, args: Dict[str, str]) -> Optional[LocationAction]:
    """
    Create a log action from the tracepoint arguments.

    :param str tp_id: the tracepoint id
    :param Dict[str, str] args: the tracepoint arguments
    :return: the new action, or None
    """
    if LOG_MSG not in args:
        return None
    if SNAPSHOT not in args or args[SNAPSHOT] != NO_COLLECT:
        return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        LOG_MSG: args[LOG_MSG],
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
    }, LocationAction.ActionType.Log)


def build_metric_action(tp_id: str, args: Dict[str, str], metrics: List[MetricDefinition]) -> Optional[LocationAction]:
    """
    Create an action to create a metric.

    :param tp_id: the tracepoint id
    :param args: the args
    :param metrics: the tracepoint metrics
    :return: the location action
    """
    if metrics is None or len(metrics) == 0:
        return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        'metrics': metrics,
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
    }, LocationAction.ActionType.Metric)


def build_span_action(tp_id: str, args: Dict[str, str]) -> Optional[LocationAction]:
    """
    Create an action to create a span.

    :param tp_id: the tracepoint id
    :param args: the args
    :return: the location action
    """
    if SPAN not in args:
        return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        SPAN: args[SPAN],
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
    }, LocationAction.ActionType.Span)


def build_trigger(tp_id: str, path: str, line_no: int, args: Dict[str, str], watches: List[str],
                  metrics: List[MetricDefinition]) -> Optional[Trigger]:
    """
    Build a trigger definition.

    :param tp_id: the tracepoint id
    :param path: the source file path
    :param line_no: the line number
    :param args: the tracepoint args
    :param watches: the watch configs
    :param metrics: the metric configs
    :return: the trigger with the actions.
    """
    stage_ = METHOD_START if METHOD_NAME in args else LINE_START

    if SPAN in args and args[SPAN] == METHOD:
        stage_ = METHOD_START

    if STAGE in args:
        stage_ = args[STAGE]

    position = Location.Position.from_stage(stage_)
    if stage_ in LINE_STAGES:
        location = LineLocation(path, line_no, position)
    elif stage_ in METHOD_STAGES:
        location = FunctionLocation(path, args.get(METHOD_NAME, None), position)
    else:
        return None

    snap_action = build_snapshot_action(tp_id, args, watches)
    log_action = build_log_action(tp_id, args)
    metric_action = build_metric_action(tp_id, args, metrics)
    span_action = build_span_action(tp_id, args)

    actions = [action for action in [snap_action, log_action, metric_action, span_action] if
               action is not None]

    return Trigger(location, actions)
