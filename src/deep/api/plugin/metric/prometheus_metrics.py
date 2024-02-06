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

"""Add support for prometheus metrics."""

import threading
from typing import Dict

import deep.logging
from deep.api.plugin import DidNotEnable
from deep.api.plugin.metric import MetricProcessor

try:
    from prometheus_client import Summary, Counter, REGISTRY, Histogram, Gauge
except ImportError as e:
    raise DidNotEnable("prometheus_client is not installed", e)


class PrometheusPlugin(MetricProcessor):
    """Connect Deep to prometheus."""

    def __init__(self, config):
        """Create new plugin."""
        super().__init__("PrometheusPlugin", config)
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
                label_keys = list(labels.keys())
                counter: Counter = self.__check_cache(name, "counter",
                                                      lambda: Counter(name=name, documentation=help_string or "",
                                                                      labelnames=label_keys,
                                                                      namespace=namespace, unit=unit))
                if len(labels) > 0:
                    counter = counter.labels(**labels)
                counter.inc(value)
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
                label_keys = list(labels.keys())
                gauge: Gauge = self.__check_cache(name, "gauge",
                                                  lambda: Gauge(name=name, documentation=help_string or "",
                                                                labelnames=label_keys,
                                                                namespace=namespace, unit=unit))
                if len(labels) > 0:
                    gauge = gauge.labels(**labels)
                gauge.inc(value)
        except Exception:
            deep.logging.exception(f"Error registering metric gauge {namespace}_{name}")
            pass

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
                label_keys = list(labels.keys())
                histogram: Histogram = self.__check_cache(name, "histogram",
                                                          lambda: Histogram(name=name, documentation=help_string or "",
                                                                            labelnames=label_keys,
                                                                            namespace=namespace, unit=unit))
                if len(labels) > 0:
                    histogram = histogram.labels(**labels)
                histogram.observe(value)
        except Exception:
            deep.logging.exception(f"Error registering metric histogram {namespace}_{name}")
            pass

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
                label_keys = list(labels.keys())
                summary: Summary = self.__check_cache(name, "summary",
                                                      lambda: Summary(name=name, documentation=help_string or "",
                                                                      labelnames=label_keys,
                                                                      namespace=namespace, unit=unit))
                if len(labels) > 0:
                    summary = summary.labels(**labels)
                summary.observe(value)
        except Exception:
            deep.logging.exception(f"Error registering metric summary {namespace}_{name}")
            pass

    @property
    def _cache(self):
        return self.__cache

    def shutdown(self):
        """Clean up and shutdown the plugin."""
        self.clear()

    def clear(self):
        """Remove any registrations."""
        with self.__lock:
            for metric in self.__cache.values():
                REGISTRY.unregister(metric)
            self.__cache = {}
