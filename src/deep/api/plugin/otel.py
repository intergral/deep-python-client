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

"""Provide plugin for Deep to connect to OTEL."""

from typing import Optional

import deep.logging
from deep.api.attributes import BoundedAttributes
from deep.api.plugin import DidNotEnable, SnapshotDecorator, ResourceProvider
from deep.api.plugin.span import SpanProcessor, Span
from deep.api.resource import Resource
from deep.processor.context.action_context import ActionContext

try:
    from opentelemetry import trace
    # noinspection PyProtectedMember
    from opentelemetry.sdk.trace import _Span, TracerProvider
except ImportError as e:
    raise DidNotEnable("opentelemetry.sdk is not installed", e)


class _OtelSpan(Span):
    """Wrap Otel span in common interface."""

    def __init__(self, proxy: _Span):
        """
        Create a new wrapper for Otel span.

        :param proxy: the underlying otel span
        """
        self.proxy = proxy

    @property
    def name(self):
        """Get the span name."""
        return self.proxy.name

    @property
    def trace_id(self):
        """Get the trace id."""
        return self.__format_trace_id(self.proxy.context.trace_id)

    @property
    def span_id(self):
        """Get the span id."""
        return self.__format_span_id(self.proxy.context.span_id)

    def add_attribute(self, key: str, value: str):
        """
        Add an attribute to the span.

        :param key: the attribute key
        :param value: the attribute value
        """
        self.proxy.set_attribute(key, value)

    def close(self):
        """Close the span."""
        if not self.proxy.end_time:
            try:
                self.proxy.end()
            except Exception:
                deep.logging.exception("failed to close span")

    @staticmethod
    def __format_span_id(_id):
        return format(_id, "016x")

    @staticmethod
    def __format_trace_id(_id):
        return format(_id, "032x")


class OTelPlugin(ResourceProvider, SnapshotDecorator, SpanProcessor):
    """
    Deep Otel plugin.

    Provide span and trace information to the snapshot.
    """

    def create_span(self, name: str) -> Optional['Span']:
        """
        Create and return a new span.

        :param name: the name of the span to create
        :return: the created span
        """
        span = trace.get_tracer("deep").start_as_current_span(name, end_on_exit=False, attributes={'dynamic': 'deep'})
        if span:
            # noinspection PyUnresolvedReferences
            # this is a generator contextlib._GeneratorContextManager
            current = span.__enter__()
            if isinstance(current, _Span):
                return _OtelSpan(current)
        return None

    def current_span(self) -> Optional['Span']:
        """
        Get the current span from the underlying provider.

        :return: the current span
        """
        span = self.__get_span()
        if span:
            return _OtelSpan(span)
        return None

    def resource(self) -> Optional[Resource]:
        """
        Provide resource.

        :return: the provided resource
        """
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            # noinspection PyUnresolvedReferences
            resource = provider.resource
            attributes = dict(resource.attributes)
            return Resource.create(attributes=attributes)
        return None

    def decorate(self, context: ActionContext) -> Optional[BoundedAttributes]:
        """
        Decorate a snapshot with additional data.

        :param context: the action context for this action

        :return: the additional attributes to attach
        """
        span = self.current_span()
        if span is not None:
            return BoundedAttributes(attributes={
                "span_name": span.name,
                "trace_id": span.trace_id,
                "span_id": span.span_id
            })
        return None

    @staticmethod
    def __get_span() -> Optional[_Span]:
        span = trace.get_current_span()
        if isinstance(span, _Span):
            return span
        return None
