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

from typing import Optional

from deep.api.attributes import BoundedAttributes
from deep.api.plugin import Plugin, DidNotEnable

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import _Span, TracerProvider
except ImportError as e:
    raise DidNotEnable("opentelemetry is not installed", e)


def span_name(span):
    # type: (_Span)-> Optional[str]
    return span.name if span.name else None


def span_id(span):
    # type: (_Span)-> Optional[str]
    return (format_span_id(span.context.span_id)) if span else None


def trace_id(span):
    # type: (_Span)-> Optional[str]
    return (format_trace_id(span.context.trace_id)) if span else None


def get_span():
    # type: () -> Optional[_Span]
    span = trace.get_current_span()
    if isinstance(span, _Span):
        return span
    return None


def format_span_id(_id):
    return format(_id, "016x")


def format_trace_id(_id):
    return format(_id, "032x")


class OTelPlugin(Plugin):

    def load_plugin(self) -> Optional[BoundedAttributes]:
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            # noinspection PyUnresolvedReferences
            resource = provider.resource
            attributes = dict(resource.attributes)
            return BoundedAttributes(attributes=attributes)
        return None

    def collect_attributes(self) -> Optional[BoundedAttributes]:
        span = get_span()
        if span is not None:
            return BoundedAttributes(attributes={
                "span_name": span_name(span),
                "trace_id": trace_id(span),
                "span_id": span_id(span)
            })
        return None
