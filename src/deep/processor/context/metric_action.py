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

"""Provide metric actions."""

from typing import List, Tuple, Dict

from deep.api.tracepoint.tracepoint_config import MetricDefinition
from deep.processor.context.action_context import ActionContext


class MetricActionContext(ActionContext):
    """Action for metrics."""

    def can_trigger(self) -> bool:
        """
        Check if the action can trigger.

        If we do not have a metric processor enabled, then skip this action.
        :return: True, if the trigger can be triggered.
        """
        if self.__has_metric_processor():
            return super().can_trigger()
        return False

    def _process_action(self):
        processors = self._parent.config.metric_processor()
        metrics = self._metrics()
        for metric in metrics:
            labels, value = self._process_metric(metric)
            for processor in processors:
                getattr(processor, self._convert_type(metric.type))(metric.name, labels, metric.namespace or "deep",
                                                                    metric.help, metric.unit, value)

    def __has_metric_processor(self):
        return len(self._parent.config.metric_processor()) > 0

    def _metrics(self) -> List[MetricDefinition]:
        return self._action.config['metrics']

    def _convert_type(self, metric_type):
        return metric_type.lower()

    def _process_metric(self, metric: MetricDefinition) -> Tuple[Dict[str, str], float]:
        metric_value = 1
        if metric.expression:
            try:
                metric_value = float(self._parent.evaluate_expression(metric.expression))
            except Exception:
                pass

        labels = {}
        if len(metric.labels) > 0:
            for label in metric.labels:
                key = label.key
                value = None
                if label.expression:
                    try:
                        value = str(self._parent.evaluate_expression(label.expression))
                    except Exception:
                        continue
                else:
                    value = label.static
                if value:
                    labels[key] = value
        return labels, metric_value
