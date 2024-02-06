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

"""Handling for OTEL metric support."""
import threading
from typing import Dict

import deep.logging
from deep.api.plugin import DidNotEnable
from deep.api.plugin.metric import MetricProcessor

try:
    from opentelemetry.metrics import get_meter, Counter, Histogram, UpDownCounter
except ImportError as e:
    raise DidNotEnable("opentelemetry.metrics is not installed", e)


class OTelMetrics(MetricProcessor):
    """
    Metric processor for otel.

    Separate from OTEL Plugin for spans, as you can have one without the other.
    """

    def __init__(self, config):
        """Create new plugin."""
        super().__init__("OTelMetrics", config)
        self.__cache = {}
        self.__lock = threading.Lock()

    def __check_cache(self, name, type_name, from_default):
        cache_key = f'{name}_{type_name}'
        if cache_key in self.__cache:
            return self.__cache[cache_key]
        default = from_default()
        self.__cache[cache_key] = default
        return default

    def counter(self, name: str, labels: Dict[str, str], namespace: str, help_string: str, unit: str, value: float):
        """
        Create a counter type value in the provider.

        :param name: the metric name
        :param labels: the metric labels
        :param namespace: the metric namespace
        :param help_string: the metric help string
        :param unit: the metric unit
        :param value: the metric value
        """
        try:
            with self.__lock:
                counter: Counter
                counter = self.__check_cache(name, 'counter',
                                             lambda: get_meter('deep').create_counter(f'{namespace}_{name}', unit,
                                                                                      help_string))
                counter.add(value, labels)
        except Exception:
            deep.logging.exception(f"Error registering metric counter {namespace}_{name}")

    def gauge(self, name: str, labels: Dict[str, str], namespace: str, help_string: str, unit: str, value: float):
        """
        Create a gauge type value in the provider.

        :param name: the metric name
        :param labels: the metric labels
        :param namespace: the metric namespace
        :param help_string: the metric help string
        :param unit: the metric unit
        :param value: the metric value
        """
        try:
            with self.__lock:
                gauge: UpDownCounter
                gauge = self.__check_cache(name, 'gauge',
                                           lambda: get_meter('deep').create_up_down_counter(f'{namespace}_{name}',
                                                                                            unit, help_string))
                gauge.add(value, labels)
        except Exception:
            deep.logging.exception(f"Error registering metric histogram {namespace}_{name}")

    def histogram(self, name: str, labels: Dict[str, str], namespace: str, help_string: str, unit: str, value: float):
        """
        Create a histogram type value in the provider.

        :param name: the metric name
        :param labels: the metric labels
        :param namespace: the metric namespace
        :param help_string: the metric help string
        :param unit: the metric unit
        :param value: the metric value
        """
        try:
            with self.__lock:
                histogram: Histogram
                histogram = self.__check_cache(name, 'histogram',
                                               lambda: get_meter('deep').create_histogram(f'{namespace}_{name}', unit,
                                                                                          help_string))
                histogram.record(value, labels)
        except Exception:
            deep.logging.exception(f"Error registering metric histogram {namespace}_{name}")

    def summary(self, name: str, labels: Dict[str, str], namespace: str, help_string: str, unit: str, value: float):
        """
        Create a summary type value in the provider.

        :param name: the metric name
        :param labels: the metric labels
        :param namespace: the metric namespace
        :param help_string: the metric help string
        :param unit: the metric unit
        :param value: the metric value
        """
        try:
            with self.__lock:
                histogram: Histogram
                histogram = self.__check_cache(name, 'summary',
                                               lambda: get_meter('deep').create_histogram(f'{namespace}_{name}', unit,
                                                                                          help_string))
                histogram.record(value, labels)
        except Exception:
            deep.logging.exception(f"Error registering metric summary {namespace}_{name}")
