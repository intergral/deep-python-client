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
from typing import Tuple

from deep.api.attributes import BoundedAttributes
from deep.api.tracepoint import EventSnapshot
from deep.api.tracepoint.constants import FRAME_TYPE, SINGLE_FRAME_TYPE, NO_FRAME_TYPE, ALL_FRAME_TYPE
from deep.api.tracepoint.trigger import LocationAction
from deep.logging.tracepoint_logger import TracepointLogger
from deep.processor.context.action_context import ActionContext
from deep.processor.context.action_results import ActionResult, ActionCallback
from deep.processor.context.log_action import LOG_MSG, LogActionContext, LogActionResult
from deep.processor.frame_collector import FrameCollectorContext, FrameCollector
from deep.processor.variable_set_processor import VariableProcessorConfig
from deep.push import PushService


class SnapshotActionContext(FrameCollectorContext, ActionContext):

    @property
    def max_tp_process_time(self) -> int:
        return self._action.config.get('MAX_TP_PROCESS_TIME', 100)

    @property
    def collection_config(self) -> VariableProcessorConfig:
        config = VariableProcessorConfig()
        config.max_string_length = self._action.config.get('MAX_STRING_LENGTH', config.DEFAULT_MAX_STRING_LENGTH)
        config.max_collection_size = self._action.config.get('MAX_COLLECTION_SIZE', config.DEFAULT_MAX_COLLECTION_SIZE)
        config.max_variables = self._action.config.get('MAX_VARIABLES', config.DEFAULT_MAX_VARIABLES)
        config.max_var_depth = self._action.config.get('MAX_VAR_DEPTH', config.DEFAULT_MAX_VAR_DEPTH)
        return config

    @property
    def ts(self) -> int:
        return self._parent.ts

    def should_collect_vars(self, frame_index: int) -> bool:
        config_type = self._action.config.get(FRAME_TYPE, SINGLE_FRAME_TYPE)
        if config_type == NO_FRAME_TYPE:
            return False
        if config_type == ALL_FRAME_TYPE:
            return True
        return frame_index == 0

    def is_app_frame(self, filename: str) -> Tuple[bool, str]:
        return self._parent.config.is_app_frame(filename)

    @property
    def watches(self):
        return self._action.config.get("watches", [])

    @property
    def log_msg(self):
        return self._action.config.get(LOG_MSG, None)

    def _process_action(self):
        collector = FrameCollector(self, self._parent.frame)

        frames, variables = collector.collect(self._parent.vars, self._parent.var_cache)

        snapshot = EventSnapshot(self._action.tracepoint, self._parent.ts, self._parent.resource, frames, variables)

        # process the snapshot watches
        for watch in self.watches:
            result, watch_lookup, _ = self.eval_watch(watch)
            snapshot.add_watch_result(result)
            snapshot.merge_var_lookup(watch_lookup)

        log_msg = self.log_msg
        if log_msg is not None:
            # create and process the log message
            context = LogActionContext(self._parent, LocationAction(self._action.id, None, {
                LOG_MSG: log_msg,
            }, LocationAction.ActionType.Log))
            log, watches, log_vars = context.process_log(log_msg)
            snapshot.log_msg = log
            for watch in watches:
                snapshot.add_watch_result(watch)
            snapshot.merge_var_lookup(log_vars)
            self._parent.attach_result(LogActionResult(context._action, log))

        self._parent.attach_result(SendSnapshotActionResult(self._action, snapshot))


class SendSnapshotActionResult(ActionResult):

    def __init__(self, action: LocationAction, snapshot: EventSnapshot):
        self.action = action
        self.snapshot = snapshot

    def collect(self, ctx_id: str, logger: TracepointLogger, service: PushService) -> ActionCallback | None:
        self.snapshot.attributes.merge_in(BoundedAttributes(attributes={'ctx_id': ctx_id}))
        service.push_snapshot(self.snapshot)
        return None
