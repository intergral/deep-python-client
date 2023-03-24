from concurrent import futures

import deepproto
import grpc
# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollResponse, ResponseType
from deepproto.proto.poll.v1.poll_pb2_grpc import PollConfigServicer
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import TracePointConfig, SnapshotResponse
from deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc import SnapshotServiceServicer


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    deepproto.proto.poll.v1.poll_pb2_grpc.add_PollConfigServicer_to_server(
        PollServicer(), server)
    deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc.add_SnapshotServiceServicer_to_server(SnapshotServicer(), server)
    server.add_insecure_port('[::]:43315')
    server.start()
    server.wait_for_termination()


class SnapshotServicer(SnapshotServiceServicer):

    def send(self, request, context):
        print(request)
        return SnapshotResponse()


class PollServicer(PollConfigServicer):
    def poll(self, request, context):
        print(request, context, context.invocation_metadata())
        response = PollResponse(ts=request.ts, current_hash="123", response=[
            TracePointConfig(id="123", path="/some/file.py", line_no=12, args={"some": "thing"},
                             watches=["some.value"])],
                                response_type=ResponseType.NO_CHANGE if request.current_hash == "123" else ResponseType.UPDATE)

        print(response)
        return response


if __name__ == '__main__':
    print("app running")
    serve()
