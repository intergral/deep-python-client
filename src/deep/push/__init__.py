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

import logging

# noinspection PyUnresolvedReferences
from deepproto.proto.common.v1.common_pb2 import KeyValue
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import Snapshot, TracePointConfig, WatchResult, Variable, \
    VariableID, StackFrame

from .push_service import PushService

__all__ = [PushService.__name__]

from ..api.tracepoint import TracePointConfig as TrPoCo, EventSnapshot, StackFrame as StFr, WatchResult as WaRe, \
    Variable as Var, VariableId as VarId
from ..grpc import convert_value


def __convert_tracepoint(tracepoint: TrPoCo):
    return TracePointConfig(ID=tracepoint.id, path=tracepoint.path, line_number=tracepoint.line_no,
                            args=tracepoint.args,
                            watches=tracepoint.watches)


def __convert_frame(frame: StFr):
    return StackFrame(file_name=frame.file_name, short_path=frame.short_path, method_name=frame.method_name,
                      line_number=frame.line_number, class_name=frame.class_name, is_async=frame.is_async,
                      column_number=frame.column_number, variables=[__convert_variable_id(v) for v in frame.variables],
                      app_frame=frame.app_frame,
                      transpiled_file_name=frame.transpiled_file_name,
                      transpiled_line_number=frame.transpiled_line_number,
                      transpiled_column_number=frame.transpiled_column_number,
                      )


def __convert_watch(watch: WaRe):
    return WatchResult(expression=watch.expression, good_result=__convert_variable_id(watch.result),
                       error_result=watch.error)


def __convert_variable(variable: Var):
    return Variable(type=variable.type, value=variable.value, hash=variable.hash,
                    children=[__convert_variable_id(c) for c in variable.children], truncated=variable.truncated)


def __convert_variable_id(variable: VarId):
    if variable is None:
        return None
    return VariableID(ID=variable.vid, name=variable.name, modifiers=variable.modifiers,
                      original_name=variable.original_name)


def __convert_lookup(var_lookup):
    converted = {}
    for k, v in var_lookup.items():
        converted[k] = __convert_variable(v)
    return converted


def convert_snapshot(snapshot: EventSnapshot) -> Snapshot:
    """
    Convert a snapshot from internal model to protobuf model.

    :param (EventSnapshot) snapshot: the internal snapshot model
    :return (Snapshot): the protobuf model of the snapshot
    """
    try:
        return Snapshot(ID=snapshot.id.to_bytes(16, "big"), tracepoint=__convert_tracepoint(snapshot.tracepoint),
                        var_lookup=__convert_lookup(snapshot.var_lookup),
                        ts_nanos=snapshot.ts_nanos, frames=[__convert_frame(f) for f in snapshot.frames],
                        watches=[__convert_watch(w) for w in snapshot.watches],
                        attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in snapshot.attributes.items()],
                        duration_nanos=snapshot.duration_nanos,
                        resource=[KeyValue(key=k, value=convert_value(v)) for k, v in
                                  snapshot.resource.attributes.items()],
                        log_msg=snapshot.log_msg)
    except Exception:
        # todo should this return None?
        logging.exception("Error converting to protobuf")
        return None
