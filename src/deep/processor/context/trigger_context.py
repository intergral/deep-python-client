
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

import uuid
from types import FrameType

from deep.api.tracepoint import Variable
from deep.api.tracepoint.trigger import LocationAction
from deep.config import ConfigService
from deep.logging.tracepoint_logger import TracepointLogger
from deep.processor.context.action_context import MetricActionContext, SpanActionContext, NoActionContext, ActionContext
from deep.processor.context.action_results import ActionResult, ActionCallback
from deep.processor.context.log_action import LogActionContext
from deep.processor.context.snapshot_action import SnapshotActionContext
from deep.processor.frame_collector import FrameCollector
from deep.processor.variable_set_processor import VariableCacheProvider
from deep.push import PushService
from deep.utils import time_ns


class TriggerContext:
    def __init__(self, config: ConfigService, push_service: PushService, frame: FrameType, event: str):
        self.__push_service = push_service
        self.__event = event
        self.__frame = frame
        self.__config = config
        self.__results: list[ActionResult] = []
        self.__ts: int = time_ns()
        self.__id: str = str(uuid.uuid4())
        self.__frame_collector: FrameCollector | None = None
        self.var_cache = VariableCacheProvider()
        self.callbacks: list[ActionCallback] = []
        self.vars: dict[str: Variable] = {}

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        for result in self.__results:
            new_callback = result.collect(self.__id, self.tracepoint_logger, self.push_service)
            if new_callback is not None:
                self.callbacks.append(new_callback)

    @property
    def file_name(self):
        return self.__frame.f_code.co_filename

    @property
    def locals(self) -> dict[str, any]:
        return self.__frame.f_locals

    @property
    def ts(self):
        return self.__ts

    @property
    def resource(self):
        return self.__config.resource

    @property
    def frame(self):
        return self.__frame

    @property
    def config(self):
        return self.__config

    def action_context(self, action: 'LocationAction') -> 'ActionContext':
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
        try:
            return eval(expression, None, self.__frame.f_locals)
        except BaseException as e:
            return e

    def attach_result(self, result: ActionResult):
        self.__results.append(result)

    @property
    def tracepoint_logger(self) -> TracepointLogger:
        return self.__config.tracepoint_logger

    @property
    def push_service(self) -> PushService:
        return self.__push_service
