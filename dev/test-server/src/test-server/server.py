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
        print("hit")
        return SnapshotResponse()


class PollServicer(PollConfigServicer):
    def poll(self, request, context):
        print(request, context, context.invocation_metadata())
        response = PollResponse(ts=request.ts, current_hash="123", response=[
            TracePointConfig(id="17", path="/simple-app/simple_test.py", line_no=17, args={"some": "thing", "fire_count": "5"}, watches=["len(uuid)", "uuid", "self.char_counter"]),
            TracePointConfig(id="2", path="/some/file_2.py", line_no=15, args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(id="2", path="/some/file_2.py", line_no=18, args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(id="5", path="/some/file.py", line_no=13, args={"some": "thing"}, watches=["some.value"]),
            TracePointConfig(id="5", path="/some/file.py", line_no=1, args={"some": "thing"}, watches=["some.value"])],
                                response_type=ResponseType.NO_CHANGE if request.current_hash == "123" else ResponseType.UPDATE)

        print(response)
        return response


if __name__ == '__main__':
    print("app running")
    serve()
