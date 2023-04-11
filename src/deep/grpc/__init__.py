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

# noinspection PyUnresolvedReferences
from deepproto.proto.common.v1.common_pb2 import KeyValue, AnyValue, ArrayValue, KeyValueList
# noinspection PyUnresolvedReferences
from deepproto.proto.resource.v1.resource_pb2 import Resource

from .grpc_service import GRPCService
from ..api.tracepoint.tracepoint_config import TracePointConfig


def convert_value(value):
    """Convert the attributes to jaeger tags."""
    if isinstance(value, bool):
        return AnyValue(bool_value=value)
    if isinstance(value, str):
        return AnyValue(string_value=value)
    if isinstance(value, int):
        return AnyValue(int_value=value)
    if isinstance(value, float):
        return AnyValue(double_value=value)
    if isinstance(value, bytes):
        return AnyValue(bytes_value=value)
    if isinstance(value, dict):
        return AnyValue(kvlist_value=value_as_dict(value))
    if isinstance(value, list):
        return AnyValue(array_value=value_as_list(value))

    return None


def value_as_dict(value):
    return KeyValueList(values=[KeyValue(key=k, value=convert_value(v)) for k, v in value.items()])


def value_as_list(value):
    return ArrayValue(values=[convert_value(val) for val in value])


def convert_resource(resource):
    return convert_attributes(resource.attributes)


def convert_attributes(attributes):
    return Resource(dropped_attributes_count=attributes.dropped,
                    attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in attributes.items()])


def convert_response(response):
    return [TracePointConfig(r.ID, r.path, r.line_no, dict(r.args), [w for w in r.watches]) for r in response]
