#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
from typing import Optional

from deep.api.attributes import BoundedAttributes
from deep.api.plugin import Plugin, DidNotEnable

try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, NonRecordingSpan
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
