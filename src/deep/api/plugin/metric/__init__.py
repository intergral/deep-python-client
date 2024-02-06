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
"""
Definition of metric processor.

Metric processor gives the ability to attach dynamic metrics to metric providers.
"""

import abc
from typing import Dict

from deep.api.plugin import Plugin


class MetricProcessor(Plugin, abc.ABC):
    """Metric processor connects Deep to a metric provider."""

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
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
        pass

    def clear(self):
        """Remove any registrations."""
        pass
