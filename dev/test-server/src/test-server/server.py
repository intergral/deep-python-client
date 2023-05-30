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
        print("hit", request.ID, request.attributes)
        return SnapshotResponse()


class PollServicer(PollConfigServicer):
    def poll(self, request, context):
        print(request, context, context.invocation_metadata())
        response = PollResponse(ts_nanos=request.ts_nanos, current_hash="123", response=[
            TracePointConfig(ID="17", path="/simple-app/simple_test.py", line_number=31,
                             args={"some": "thing", "fire_count": "-1", "fire_period": "1000"},
                             watches=["len(uuid)", "uuid", "self.char_counter"]),
            TracePointConfig(ID="2", path="/some/file_2.py", line_number=15,
                             args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(ID="2", path="/some/file_2.py", line_number=18,
                             args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(ID="5", path="/some/file.py", line_number=13,
                             args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(ID="5", path="/some/file.py", line_number=1,
                             args={"some": "thing"}, watches=["some.value"])],
                                response_type=ResponseType.NO_CHANGE if request.current_hash == "123"
                                else ResponseType.UPDATE)

        print(response)
        return response


if __name__ == '__main__':
    print("app running")
    serve()
