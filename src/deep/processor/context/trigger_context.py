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

"""A context for the handling of a trigger."""

import uuid
from types import FrameType
from typing import Dict, Optional, List

import deep.logging
from deep.api.plugin import TracepointLogger
from deep.api.tracepoint import Variable
from deep.api.tracepoint.trigger import LocationAction
from deep.config import ConfigService
from deep.processor.context.action_context import NoActionContext, ActionContext
from deep.processor.context.action_results import ActionResult, ActionCallback
from deep.processor.context.log_action import LogActionContext
from deep.processor.context.metric_action import MetricActionContext
from deep.processor.context.snapshot_action import SnapshotActionContext
from deep.processor.context.span_action import SpanActionContext
from deep.processor.frame_collector import FrameCollector
from deep.processor.variable_set_processor import VariableCacheProvider
from deep.push import PushService
from deep.utils import time_ns


class TriggerContext:
    """
    Context for a trigger.

    A context is created in a valid location is triggered. This context is then used to process all the actions,
    collect the data and ship of the results.
    """

    def __init__(self, config: ConfigService, push_service: PushService, frame: FrameType, event: str):
        """
        Create a new trigger context.

        :param config: the config service
        :param push_service: the push service
        :param frame: the frame data
        :param event: the trigger event
        """
        self.__push_service = push_service
        self.__event = event
        self.__frame = frame
        self.__config = config
        self.__results: List[ActionResult] = []
        self.__ts: int = time_ns()
        self.__id: str = str(uuid.uuid4())
        self.__frame_collector: Optional[FrameCollector] = None
        self.var_cache = VariableCacheProvider()
        self.callbacks: List[ActionCallback] = []
        self.vars: Dict[str: Variable] = {}

    def __enter__(self):
        """Start the 'with' statement and open this context."""
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Complete the 'with' statement, and close this context."""
        for result in self.__results:
            try:
                new_callback = result.process(self)
                if new_callback is not None:
                    self.callbacks.append(new_callback)
            except Exception:
                deep.logging.exception("failed to process result {}", result)

    @property
    def id(self):
        """The trigger context id."""
        return self.__id

    @property
    def file_name(self):
        """The trigger location source file name."""
        return self.__frame.f_code.co_filename

    @property
    def locals(self) -> Dict[str, any]:
        """The local frame variables."""
        return self.__frame.f_locals

    @property
    def ts(self):
        """The timestamp in nanoseconds for this trigger."""
        return self.__ts

    @property
    def resource(self):
        """The client resource information."""
        return self.__config.resource

    @property
    def frame(self):
        """The raw frame data."""
        return self.__frame

    @property
    def config(self) -> ConfigService:
        """The config service."""
        return self.__config

    def action_context(self, action: 'LocationAction') -> 'ActionContext':
        """
        Create an action context from this context, for the provided action.

        :param action: the action
        :return: the new action context.
        """
        if action.action_type == LocationAction.ActionType.Snapshot:
            return SnapshotActionContext(self, action)
        if action.action_type == LocationAction.ActionType.Log:
            return LogActionContext(self, action)
        if action.action_type == LocationAction.ActionType.Metric:
            return MetricActionContext(self, action)
        if action.action_type == LocationAction.ActionType.Span:
            return SpanActionContext(self, action)
        return NoActionContext(self, action)

    def evaluate_expression(self, expression: str) -> any:
        """
        Evaluate an expression to a value.

        :param expression: the expression
        :return: the result of the expression, or the exception that was raised.
        """
        try:
            return eval(expression, None, self.__frame.f_locals)
        except BaseException as e:
            return e

    def attach_result(self, result: ActionResult):
        """
        Attach a result for this context.

        :param result: the new result
        """
        self.__results.append(result)

    @property
    def tracepoint_logger(self) -> TracepointLogger:
        """The tracepoint logger service."""
        return self.__config.tracepoint_logger

    @property
    def push_service(self) -> PushService:
        """The push service."""
        return self.__push_service
