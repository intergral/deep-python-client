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
    return [TracePointConfig(r.ID, r.path, r.line_number, dict(r.args), [w for w in r.watches]) for r in response]
