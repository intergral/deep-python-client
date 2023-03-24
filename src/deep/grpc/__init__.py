# noinspection PyUnresolvedReferences
from deepproto.proto.common.v1.common_pb2 import KeyValue, AnyValue, ArrayValue, KeyValueList
# noinspection PyUnresolvedReferences
from deepproto.proto.resource.v1.resource_pb2 import Resource

from .grpc_service import GRPCService
from ..api.tracepoint.tracepoint_config import TracepointConfig


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
    pb_resource = Resource(dropped_attributes_count=resource.attributes.dropped,
                           attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in resource.attributes.items()])

    return pb_resource


def convert_response(response):
    return [TracepointConfig(r.id, r.path, r.line_no, dict(r.args), [w for w in r.watches]) for r in response]
