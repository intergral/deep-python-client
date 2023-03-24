from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.api.tracepoint import TracePointConfig, EventSnapshot
from deep.config import ConfigService
from deep.processor.frame_collector import FrameCollector


class FrameProcessor(FrameCollector):
    _filtered_tracepoints: list[TracePointConfig]

    def __init__(self, tracepoints: list[TracePointConfig], frame, config: ConfigService):
        super().__init__(frame, config)
        self._tracepoints = tracepoints
        self._filtered_tracepoints = []

    def collect(self):
        snapshots = []
        stack, variables = self.process_frame()
        for tp in self._filtered_tracepoints:
            snapshot = EventSnapshot(tp, stack, variables)
            for watch in tp.watches:
                result, watch_lookup = self.eval_watch(watch)
                snapshot.add_watch_result(result, watch_lookup)
            attributes = self.process_attributes(tp)
            snapshot.attributes.merge_in(attributes)
            snapshots.append(snapshot)
            tp.has_triggered(self._ts)

        return snapshots

    def can_collect(self):
        for tp in self._tracepoints:
            if tp.can_trigger(self._ts) and self.condition_passes(tp):
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
        except:
            logging.exception("Error evaluating condition %s", condition)
            return False

    def configure_self(self):
        for tp in self._filtered_tracepoints:
            self._frame_config.process_tracepoint(tp)
        self._frame_config.close()

    def process_attributes(self, tp):
        return BoundedAttributes()
