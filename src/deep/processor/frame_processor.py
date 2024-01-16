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

"""
Handle Frame data processing.

When processing a frame we need to ensure that the matched tracepoints can fire and that we collect
the appropriate information. We need to process the conditions and fire rates of the tracepoints, and check the
configs to collect the smallest amount of data possible.
"""

from types import FrameType
from typing import List

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.api.tracepoint import TracePointConfig, EventSnapshot
from deep.api.tracepoint.tracepoint_config import LOG_MSG
from deep.config import ConfigService
from deep.processor.frame_collector import FrameCollector


class FrameProcessor(FrameCollector):
    """This handles a 'hit' and starts the process of collecting the data."""

    _filtered_tracepoints: List[TracePointConfig]

    def __init__(self, tracepoints: List[TracePointConfig], frame: FrameType, config: ConfigService):
        """
        Create a new processor.

        :param tracepoints: the tracepoints for the triggering event
        :param frame: the frame data
        :param config: the deep config service
        """
        super().__init__(frame, config)
        self._tracepoints = tracepoints
        self._filtered_tracepoints = []

    def collect(self) -> list[EventSnapshot]:
        """
        Collect the snapshot data for the available tracepoints.

        :return: list of completed snapshots
        """
        snapshots = []
        # process the frame to a stack and var list
        stack, variables = self.process_frame()
        # iterate the tracepoints
        for tp in self._filtered_tracepoints:
            # crete a snapshot
            snapshot = EventSnapshot(tp, self._ts, self._config.resource, stack, variables)
            # process the snapshot watches
            for watch in tp.watches:
                result, watch_lookup, _ = self.eval_watch(watch)
                snapshot.add_watch_result(result)
                snapshot.merge_var_lookup(watch_lookup)

            log_msg = tp.get_arg(LOG_MSG, None)
            if log_msg is not None:
                processed_log, watch_results, watch_lookup = self.process_log(tp, log_msg)
                snapshot.log_msg = processed_log
                for watch in watch_results:
                    snapshot.add_watch_result(watch)
                snapshot.merge_var_lookup(watch_lookup)
                self.log_tracepoint(processed_log, tp.id, format(snapshot.id, "016x"))

            # process the snapshot attributes
            attributes = self.process_attributes(tp)
            snapshot.attributes.merge_in(attributes)
            # save the snapshot
            snapshots.append(snapshot)
            # mark tp as triggered
            tp.record_triggered(self._ts)

        return snapshots

    def can_collect(self):
        """
        Check if we can collect data.

        Check if the tracepoints can fire given their configs. Checking time windows, fire rates etc.

        :return: True, if any tracepoint can fire
        """
        for tp in self._tracepoints:
            if tp.can_trigger(self._ts) and self.condition_passes(tp):
                # store the filtered tracepoints in a new list
                self._filtered_tracepoints.append(tp)

        return len(self._filtered_tracepoints) > 0

    def condition_passes(self, tp: TracePointConfig) -> bool:
        """
        Check if the tracepoint condition passes.

        :param (TracePointConfig) tp: the tracepoint to check
        :return: True, if the condition passes
        """
        condition = tp.condition
        if condition is None or condition == "":
            # There is no condition so return True
            return True
        logging.debug("Executing condition evaluation: %s", condition)
        try:
            result = eval(condition, None, self._frame.f_locals)
            logging.debug("Condition result: %s", result)
            if result:
                return True
            return False
        except Exception:
            logging.exception("Error evaluating condition %s", condition)
            return False

    def configure_self(self):
        """Process the filtered tracepoints to configure this processor."""
        for tp in self._filtered_tracepoints:
            self._frame_config.process_tracepoint(tp)
        self._frame_config.close()

    def process_attributes(self, tp: TracePointConfig) -> BoundedAttributes:
        """
        Process the attributes for a tracepoint.

        :param (TracePointConfig) tp: the tracepoint to process.
        :return (BoundedAttributes): the attributes for the tracepoint
        """
        attributes = {
            "tracepoint": tp.id,
            "path": tp.path,
            "line": tp.line_no,
            "stack": tp.stack_type,
            "frame": tp.frame_type
        }
        if len(tp.watches) != 0:
            attributes["has_watches"] = True
        if tp.condition is not None:
            attributes["has_condition"] = True
        return BoundedAttributes(attributes=attributes)
