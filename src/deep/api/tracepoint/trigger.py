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
import abc
from enum import Enum

from typing import Optional

from deep.api.tracepoint.constants import WINDOW_START, WINDOW_END, FIRE_COUNT, FIRE_PERIOD, LOG_MSG, WATCHES, \
    LINE_START, METHOD_START, METHOD_END, LINE_END, LINE_CAPTURE, METHOD_CAPTURE, NO_COLLECT, SNAPSHOT, CONDITION, \
    FRAME_TYPE, STACK_TYPE, SINGLE_FRAME_TYPE, STACK, SPAN, STAGE, METHOD_NAME, LINE_STAGES, METHOD_STAGES
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
        Snapshot = 1
        Log = 2
        Metric = 3
        Span = 4

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.name

    def __init__(self, tp_id: str, condition: str | None, config: dict[str, any], action_type: ActionType):
        self.__id = tp_id
        self.__condition = condition
        self.__config = config
        self.__window = TracepointWindow(self.__config.get(WINDOW_START, 0), self.__config.get(WINDOW_END, 0))
        self.__stats = TracepointExecutionStats()
        self.__action_type = action_type
        self.__location: 'Location | None' = None

    @property
    def id(self) -> str:
        """
        The id of the tracepoint that created this action.

        :return: the tracepoint id
        """
        return self.__id

    @property
    def condition(self) -> str | None:
        """
        The condition that is set on the tracepoint
        :return: the condition if set
        """
        return self.__condition

    @property
    def config(self) -> dict[str, any]:
        """
        The config for this action.

        :return: the full action config.
        """
        return self.__config

    @property
    def fire_count(self):
        """
        Get the allowed number of triggers

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
        return self.__action_type

    @property
    def tracepoint(self):
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
        trigger = self._can_trigger(ts)
        return trigger

    def _can_trigger(self, ts):
        """
        Check if the tracepoint can trigger, this is to check the config. e.g. fire count, fire windows etc
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
        """This is called when the tracepoint has been processed."""
        self.__stats.fire(ts)

    def __get_int(self, name: str, default_value: int):
        try:
            return int(self.__config.get(name, default_value))
        except ValueError:
            return default_value

    def __str__(self):
        return str({
            'id': self.__id,
            'condition': self.__condition,
            'config': self.__config,
            'type': self.__action_type
        })

    def __repr__(self):
        return self.__str__()

    def __eq__(self, __value):
        if self.__id == __value.__id and self.__condition == __value.__condition and self.__config == __value.__config:
            return True
        return False

    def with_location(self, location: 'Location') -> 'LocationAction':
        self.__location = location
        return self


class Location(abc.ABC):
    class Position(Enum):
        START = 1
        END = 2
        CAPTURE = 3

        @classmethod
        def from_stage(cls, stage_):
            if stage_ in [LINE_START, METHOD_START]:
                return Location.Position.START
            if stage_ in [LINE_END, METHOD_END]:
                return Location.Position.END
            if stage_ in [LINE_CAPTURE, METHOD_CAPTURE]:
                return Location.Position.CAPTURE
            return Location.Position.START

    def __init__(self, position: Position = None):
        self.position = position

    @abc.abstractmethod
    def at_location(self, event: str, file: str, line: int, method: str) -> bool:
        pass

    @property
    @abc.abstractmethod
    def id(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def path(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def line(self) -> int:
        pass


class Trigger(Location):
    def __init__(self, location: Location, actions: list[LocationAction]):
        super().__init__()
        self.__location = location
        self.__actions = actions

    def at_location(self, event: str, file: str, line: int, method: str) -> bool:
        return self.__location.at_location(event, file, line, method)

    @property
    def actions(self) -> list[LocationAction]:
        return [action.with_location(self) for action in self.__actions]

    @property
    def id(self):
        return self.__location.id

    @property
    def path(self):
        return self.__location.path

    @property
    def line(self):
        return self.__location.line

    def __str__(self):
        return str({
            'location': self.__location,
            'actions': self.__actions
        })

    def __repr__(self):
        return self.__str__()

    def __eq__(self, __value):
        if self.__location == __value.__location and self.__actions == __value.__actions:
            return True
        return False

    def merge_actions(self, actions: list[LocationAction]):
        self.__actions += actions


class LineLocation(Location):

    def __init__(self, path: str, line: int, position: Location.Position):
        super().__init__(position)
        self.__path = path
        self.__line = line

    def at_location(self, event: str, file: str, line: int, method: str):
        if event == "line" and file == self.path and line == self.line:
            return True
        return False

    @property
    def id(self):
        return "%s#%s" % (self.path, self.line)

    @property
    def path(self):
        return self.__path

    @property
    def line(self):
        return self.__line

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, __value):
        if self.path == __value.path and self.line == __value.line:
            return True
        return False


class MethodLocation(Location):
    def __init__(self, path: str, method: str, position: Location.Position):
        super().__init__(position)
        self.method = method
        self.__path = path

    def at_location(self, event: str, file: str, line: int, method: str):
        if event == "CALL" and method == self.method and file == self.path:
            return True
        return False

    @property
    def id(self):
        return "%s#%s" % (self.path, self.method)

    @property
    def path(self):
        return self.__path

    @property
    def line(self):
        return -1

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, __value):
        if self.path == __value.path and self.method == __value.method:
            return True
        return False


def build_snapshot_action(tp_id: str, args: dict[str, str], watches: list[str]) -> Optional[LocationAction]:
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


def build_log_action(tp_id: str, args: dict[str, str]) -> Optional[LocationAction]:
    """
    Create a log action from the tracepoint arguments

    :param str tp_id: the tracepoint id
    :param dict[str, str] args: the tracepoint arguments
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


def build_metric_action(tp_id: str, args: dict[str, str], metrics: list[MetricDefinition]) -> Optional[LocationAction]:
    if metrics is None or len(metrics) == 0:
        return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        'metrics': metrics,
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
    }, LocationAction.ActionType.Metric)


def build_span_action(tp_id: str, args: dict[str, str]) -> Optional[LocationAction]:
    if SPAN not in args:
        return None

    condition = args[CONDITION] if CONDITION in args else None
    return LocationAction(tp_id, condition, {
        SPAN: args[SPAN],
        FIRE_COUNT: args.get(FIRE_COUNT, '1'),
        FIRE_PERIOD: args.get(FIRE_PERIOD, '1000'),
    }, LocationAction.ActionType.Snapshot)


def build_trigger(tp_id: str, path: str, line_no: int, args: dict[str, str], watches: list[str],
                  metrics: list[MetricDefinition]) -> Optional[Trigger]:
    stage_ = METHOD_START if METHOD_NAME in args else LINE_START
    if STAGE in args:
        stage_ = args[STAGE]

    if stage_ in LINE_STAGES:
        location = LineLocation(path, line_no, Location.Position.from_stage(stage_))
    elif stage_ in METHOD_STAGES:
        location = MethodLocation(path, args[METHOD_NAME], Location.Position.from_stage(stage_))
    else:
        return None

    snap_action = build_snapshot_action(tp_id, args, watches)
    log_action = build_log_action(tp_id, args)
    metric_action = build_metric_action(tp_id, args, metrics)
    span_action = build_span_action(tp_id, args)

    actions = [action for action in [snap_action, log_action, metric_action, span_action] if
               action is not None]

    return Trigger(location, actions)
