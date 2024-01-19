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

"""
Collection of functions to convert to protobuf version of types.

We do not use the protobuf types throughout the project as they do not autocomplete or
have type definitions that work in IDE. It also makes it easier to deal with agent functionality by
having local types we can modify.
"""
from typing import List, Dict

# noinspection PyUnresolvedReferences
from deepproto.proto.common.v1.common_pb2 import KeyValue, AnyValue, ArrayValue, KeyValueList
# noinspection PyUnresolvedReferences
from deepproto.proto.resource.v1.resource_pb2 import Resource
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import MetricType

from .grpc_service import GRPCService  # noqa: F401
from ..api.tracepoint.tracepoint_config import LabelExpression, MetricDefinition
from ..api.tracepoint.trigger import build_trigger, Trigger


def convert_value(value):
    """
    Convert a value from the python type.

    :param value: the value to convert
    :return: the value wrapped in the appropriate AnyValue type.
    """
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
        return AnyValue(kvlist_value=__value_as_dict(value))
    if isinstance(value, list):
        return AnyValue(array_value=__value_as_list(value))

    return None


def __value_as_dict(value):
    return KeyValueList(values=[KeyValue(key=k, value=convert_value(v)) for k, v in value.items()])


def __value_as_list(value):
    return ArrayValue(values=[convert_value(val) for val in value])


def convert_resource(resource):
    """
    Convert an internal resource to GRPC type.

    :param resource: the resource to convert
    :return: the converted type as GRPC.
    """
    return __convert_attributes(resource.attributes)


def __convert_attributes(attributes):
    return Resource(dropped_attributes_count=attributes.dropped,
                    attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in attributes.items()])


def __convert_static_value(value):
    static_value = value.static
    set_field = static_value.WhichOneof("value")
    if set_field is None:
        return None
    return getattr(static_value, set_field)


def convert_label_expressions(label_expressions) -> List[LabelExpression]:
    """
    Convert a label expression.

    :param label_expressions: the expression to convert.
    :return: the converted expression
    """
    return [LabelExpression(label.key, __convert_static_value(label), label.expression) for
            label in label_expressions]


def __convert_metric_definition(metrics):
    return [MetricDefinition(m.name, MetricType.Name(metrics[0].type), convert_label_expressions(m.labelExpressions),
                             m.expression, m.namespace, m.help, m.unit) for m in metrics]


def convert_response(response) -> List[Trigger]:
    """
    Convert a response from GRPC to internal types.

    This function should create a list of Triggers from the incoming configuration. The Trigger should be a
    location with one or more actions to perform at that location.

    :param response: the response from the poll request
    :return: a list of trigger locations with the appropriate actions
    """
    all_triggers: Dict[str, Trigger] = {}
    for r in response:
        # from the incoming tracepoints create a Trigger with actions
        trigger = build_trigger(r.ID, r.path, r.line_number, dict(r.args), [w for w in r.watches],
                                __convert_metric_definition(r.metrics))
        location_id = trigger.id
        # if we already have a trigger for this location then merge the new actions into it
        if location_id in all_triggers:
            all_triggers[location_id].merge_actions(trigger.actions)
        else:
            all_triggers[location_id] = trigger

    return list(all_triggers.values())
