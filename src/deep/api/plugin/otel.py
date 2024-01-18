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

from deep.api.attributes import BoundedAttributes
from deep.api.plugin import Plugin, DidNotEnable

try:
    from opentelemetry import trace
    # noinspection PyProtectedMember
    from opentelemetry.sdk.trace import _Span, TracerProvider
except ImportError as e:
    raise DidNotEnable("opentelemetry is not installed", e)


class OTelPlugin(Plugin):
    """
    Deep Otel plugin.

    Provide span and trace information to the snapshot.
    """

    def load_plugin(self) -> Optional[BoundedAttributes]:
        """
        Load the plugin.

        :return: any values to attach to the client resource.
        """
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            # noinspection PyUnresolvedReferences
            resource = provider.resource
            attributes = dict(resource.attributes)
            return BoundedAttributes(attributes=attributes)
        return None

    def collect_attributes(self) -> Optional[BoundedAttributes]:
        """
        Collect attributes to attach to snapshot.

        :return: the attributes to attach.
        """
        span = OTelPlugin.__get_span()
        if span is not None:
            return BoundedAttributes(attributes={
                "span_name": OTelPlugin.__span_name(span),
                "trace_id": OTelPlugin.__trace_id(span),
                "span_id": OTelPlugin.__span_id(span)
            })
        return None

    @staticmethod
    def __span_name(span):
        # type: (_Span)-> Optional[str]
        return span.name if span.name else None

    @staticmethod
    def __span_id(span):
        # type: (_Span)-> Optional[str]
        return (OTelPlugin.__format_span_id(span.context.span_id)) if span else None

    @staticmethod
    def __trace_id(span):
        # type: (_Span)-> Optional[str]
        return (OTelPlugin.__format_trace_id(span.context.trace_id)) if span else None

    @staticmethod
    def __get_span():
        # type: () -> Optional[_Span]
        span = trace.get_current_span()
        if isinstance(span, _Span):
            return span
        return None

    @staticmethod
    def __format_span_id(_id):
        return format(_id, "016x")

    @staticmethod
    def __format_trace_id(_id):
        return format(_id, "032x")
