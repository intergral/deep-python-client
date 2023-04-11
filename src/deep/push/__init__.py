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


def convert_tracepoint(tracepoint: TrPoCo):
    return TracePointConfig(ID=tracepoint.id, path=tracepoint.path, line_no=tracepoint.line_no, args=tracepoint.args,
                            watches=tracepoint.watches)


def convert_frame(frame: StFr):
    return StackFrame(file_name=frame.file_name, method_name=frame.method_name, line_number=frame.line_number,
                      class_name=frame.class_name, is_async=frame.is_async, column_number=frame.column_number,
                      variables=[convert_variable_id(v) for v in frame.variables], app_frame=frame.app_frame,
                      transpiled_file_name=frame.transpiled_file_name,
                      transpiled_line_number=frame.transpiled_line_number,
                      transpiled_column_number=frame.transpiled_column_number,
                      )


def convert_watch(watch: WaRe):
    return WatchResult(expression=watch.expression, good_result=convert_variable_id(watch.result),
                       error_result=watch.error)


def convert_variable(variable: Var):
    return Variable(type=variable.type, value=variable.value, hash=variable.hash,
                    children=[convert_variable_id(c) for c in variable.children], truncated=variable.truncated)


def convert_variable_id(variable: VarId):
    if variable is None:
        return None
    return VariableID(ID=variable.vid, name=variable.name, modifiers=variable.modifiers)


def convert_lookup(var_lookup):
    converted = {}
    for k, v in var_lookup.items():
        converted[k] = convert_variable(v)
    return converted


def convert_snapshot(snapshot: EventSnapshot) -> Snapshot:
    try:
        return Snapshot(ID=snapshot.id.to_bytes(16, "big"), tracepoint=convert_tracepoint(snapshot.tracepoint),
                        var_lookup=convert_lookup(snapshot.var_lookup),
                        ts=snapshot.ts, frames=[convert_frame(f) for f in snapshot.frames],
                        watches=[convert_watch(w) for w in snapshot.watches],
                        attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in snapshot.attributes.items()],
                        nanos_duration=snapshot.nanos_duration,
                        resource=[KeyValue(key=k, value=convert_value(v)) for k, v in
                                  snapshot.resource.attributes.items()])
    except Exception:
        logging.exception("Error converting to protobuf")
        return Snapshot()
