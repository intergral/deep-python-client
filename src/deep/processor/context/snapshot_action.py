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

"""Handling for snapshot actions."""

from typing import Tuple, Optional, TYPE_CHECKING

import deep.logging
from deep.api.attributes import BoundedAttributes
from deep.api.tracepoint import EventSnapshot
from deep.api.tracepoint.constants import FRAME_TYPE, SINGLE_FRAME_TYPE, NO_FRAME_TYPE, ALL_FRAME_TYPE
from deep.api.tracepoint.trigger import LocationAction
from deep.processor.context.action_context import ActionContext
from deep.processor.context.action_results import ActionResult, ActionCallback
from deep.processor.context.log_action import LOG_MSG, LogActionContext, LogActionResult
from deep.processor.frame_collector import FrameCollectorContext, FrameCollector
from deep.processor.variable_set_processor import VariableProcessorConfig

if TYPE_CHECKING:
    from deep.processor.context.trigger_context import TriggerContext


class SnapshotActionContext(FrameCollectorContext, ActionContext):
    """The context to use when capturing a snapshot."""

    @property
    def max_tp_process_time(self) -> int:
        """The max time to spend processing a tracepoint."""
        return self.location_action.config.get('MAX_TP_PROCESS_TIME', 100)

    @property
    def collection_config(self) -> VariableProcessorConfig:
        """The variable processing config."""
        config = VariableProcessorConfig()
        config.max_string_length = self.location_action.config.get('MAX_STRING_LENGTH',
                                                                   config.DEFAULT_MAX_STRING_LENGTH)
        config.max_collection_size = self.location_action.config.get('MAX_COLLECTION_SIZE',
                                                                     config.DEFAULT_MAX_COLLECTION_SIZE)
        config.max_variables = self.location_action.config.get('MAX_VARIABLES', config.DEFAULT_MAX_VARIABLES)
        config.max_var_depth = self.location_action.config.get('MAX_VAR_DEPTH', config.DEFAULT_MAX_VAR_DEPTH)
        return config

    @property
    def ts(self) -> int:
        """The timestamp in nanoseconds for this trigger."""
        return self.trigger_context.ts

    def should_collect_vars(self, current_frame_index: int) -> bool:
        """
        Check if we can collect data for a frame.

        Frame indexes start from 0 (as the current frame) and increase as we go back up the stack.

        :param (int) current_frame_index: the current frame index.
        :return (bool): if we should collect the frame vars.
        """
        config_type = self.location_action.config.get(FRAME_TYPE, SINGLE_FRAME_TYPE)
        if config_type == NO_FRAME_TYPE:
            return False
        if config_type == ALL_FRAME_TYPE:
            return True
        return current_frame_index == 0

    def is_app_frame(self, filename: str) -> Tuple[bool, str]:
        """
        Check if the current frame is a user application frame.

        :param filename: the frame file name
        :return: True if add frame, else False
        """
        return self.trigger_context.config.is_app_frame(filename)

    @property
    def watches(self):
        """The configured watches."""
        return self.location_action.config.get("watches", [])

    @property
    def log_msg(self):
        """The configured log message on the tracepoint."""
        return self.location_action.config.get(LOG_MSG, None)

    def _process_action(self):
        collector = FrameCollector(self, self.trigger_context.frame)

        frames, variables = collector.collect(self.trigger_context.vars, self.trigger_context.var_cache)

        snapshot = EventSnapshot(self.location_action.tracepoint, self.trigger_context.ts,
                                 self.trigger_context.resource, frames, variables)

        # process the snapshot watches
        for watch in self.watches:
            result, watch_lookup, _ = self.eval_watch(watch)
            snapshot.add_watch_result(result)
            snapshot.merge_var_lookup(watch_lookup)

        log_msg = self.log_msg
        if log_msg is not None:
            # create and process the log message
            context = LogActionContext(self.trigger_context, LocationAction(self.location_action.id, None, {
                LOG_MSG: log_msg,
            }, LocationAction.ActionType.Log))
            log, watches, log_vars = context.process_log(log_msg)
            snapshot.log_msg = log
            for watch in watches:
                snapshot.add_watch_result(watch)
            snapshot.merge_var_lookup(log_vars)
            self.trigger_context.attach_result(LogActionResult(context.location_action, log))

        self.trigger_context.attach_result(SendSnapshotActionResult(self, snapshot))


class SendSnapshotActionResult(ActionResult):
    """The result of a successful snapshot action."""

    def __init__(self, action_context: ActionContext, snapshot: EventSnapshot):
        """
        Create a new snapshot action result.

        :param action_context: the action context that created this result
        :param snapshot: the snapshot result
        """
        self.action_context = action_context
        self.snapshot = snapshot

    def process(self, ctx: 'TriggerContext') -> Optional[ActionCallback]:
        """
        Process this result.

        :param ctx: the triggering context

        :return: an action callback if we need to do something at the 'end', or None
        """
        attributes = BoundedAttributes(attributes={'ctx_id': ctx.id}, immutable=False)
        for decorator in ctx.config.snapshot_decorators:
            try:
                decorate = decorator.decorate(self.action_context)
                if decorate is not None:
                    attributes.merge_in(decorate)
            except Exception:
                deep.logging.exception("Failed to decorate snapshot: %s ", decorator)

        self.snapshot.attributes.merge_in(attributes)
        ctx.push_service.push_snapshot(self.snapshot)
        return None
