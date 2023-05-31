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
from typing import List

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.api.tracepoint import TracePointConfig, EventSnapshot
from deep.config import ConfigService
from deep.processor.frame_collector import FrameCollector


class FrameProcessor(FrameCollector):
    """
    This handles a 'hit' and starts the process of collecting the data.
    """
    _filtered_tracepoints: List[TracePointConfig]

    def __init__(self, tracepoints: List[TracePointConfig], frame, config: ConfigService):
        super().__init__(frame, config)
        self._tracepoints = tracepoints
        self._filtered_tracepoints = []

    def collect(self):
        """
        Here we start the data collection process
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
                result, watch_lookup = self.eval_watch(watch)
                snapshot.add_watch_result(result, watch_lookup)
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
        Check if the tracepoints can fire given their configs. Checking time windows, fire rates etc.
        :return: True, if any tracepoint can fire
        """
        for tp in self._tracepoints:
            if tp.can_trigger(self._ts) and self.condition_passes(tp):
                # store the filtered tracepoints in a new list
                self._filtered_tracepoints.append(tp)

        return len(self._filtered_tracepoints) > 0

    def condition_passes(self, tp):
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
        """
        Using the filtered tracepoints, re-configure the frame config for minimum collection
        :return:
        """
        for tp in self._filtered_tracepoints:
            self._frame_config.process_tracepoint(tp)
        self._frame_config.close()

    def process_attributes(self, tp):
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
