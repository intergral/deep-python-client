# noinspection PyUnresolvedReferences
from deepproto.proto.common.v1.common_pb2 import KeyValue
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import Snapshot, TracePointConfig, WatchResult, Variable, \
    VariableId, StackFrame

from .push_service import PushService

__all__ = [PushService.__name__]

from ..api.tracepoint import TracePointConfig as TrPoCo, EventSnapshot, StackFrame as StFr, WatchResult as WaRe, \
    Variable as Var, VariableId as VarId
from ..grpc import convert_value


def convert_tracepoint(tracepoint: TrPoCo):
    return TracePointConfig(id=tracepoint.id, path=tracepoint.path, line_no=tracepoint.line_no, args=tracepoint.args,
                            watches=tracepoint.watches)


def convert_frame(frame: StFr):
    return StackFrame(file_name=frame.file_name, method_name=frame.method_name, line_number=frame.line_number,
                      class_name=frame.class_name, is_async=frame.is_async, column_number=frame.column_number,
                      transpiled_file_name=frame.transpiled_file_name,
                      transpiled_line_number=frame.transpiled_line_number,
                      transpiled_column_number=frame.transpiled_column_number,
                      variables=[convert_variable_id(v) for v in frame.variables], app_frame=frame.app_frame)


def convert_watch(watch: WaRe):
    return WatchResult(expression=watch.expression, result=convert_variable_id(watch.result))


def convert_variable(variable: Var):
    return Variable(type=variable.type, value=variable.value, hash=variable.hash,
                    children=[convert_variable_id(c) for c in variable.children], truncated=variable.truncated)


def convert_variable_id(variable: VarId):
    return VariableId(id=variable.vid, name=variable.name, modifiers=variable.modifiers)


def convert_snapshot(snapshot: EventSnapshot) -> Snapshot:
    return Snapshot(id=snapshot.id, tracepoint=convert_tracepoint(snapshot.tracepoint), var_lookup=snapshot.var_lookup,
                    ts=snapshot.ts, frames=[convert_frame(f) for f in snapshot.frames],
                    watches=[convert_watch(w) for w in snapshot.watches],
                    attributes=[KeyValue(key=k, value=convert_value(v)) for k, v in snapshot.attributes.items()],
                    nanos_duration=snapshot.nanos_duration,
                    resource=[KeyValue(key=k, value=convert_value(v)) for k, v in snapshot.resource.attributes.items()])
