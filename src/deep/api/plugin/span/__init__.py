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
Definition of span processor.

Span processor gives the ability to generate spans dynamically.
"""

import abc
from typing import Optional

from deep.api.plugin import Plugin


class SpanProcessor(Plugin, abc.ABC):
    """Span processor connects Deep to a span provider."""

    @abc.abstractmethod
    def create_span(self, name: str) -> Optional['Span']:
        """
        Create and return a new span.

        :param name: the name of the span to create
        :return: the created span
        """
    pass

    @abc.abstractmethod
    def current_span(self) -> Optional['Span']:
        """
        Get the current span from the underlying provider.

        :return: the current span
        """
        pass


class Span:
    """Internal type to wrap spans."""

    @property
    @abc.abstractmethod
    def name(self):
        """Get the span name."""
        pass

    @property
    @abc.abstractmethod
    def trace_id(self):
        """Get the trace id."""
        pass

    @property
    @abc.abstractmethod
    def span_id(self):
        """Get the span id."""
        pass

    @abc.abstractmethod
    def add_attribute(self, key: str, value: str):
        """
        Add an attribute to the span.

        :param key: the attribute key
        :param value: the attribute value
        """
        pass

    @abc.abstractmethod
    def close(self):
        """Close the span."""
        pass
