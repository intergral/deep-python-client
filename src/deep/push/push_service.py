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

from deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc import SnapshotServiceStub

from deep import logging
from deep.api.tracepoint import EventSnapshot
from deep.utils import snapshot_id_as_hex_str


class PushService:
    """
    This service deals with pushing the snapshots to the service endpoints
    """
    def __init__(self, config, grpc, task_handler):
        self.config = config
        self.grpc = grpc
        self.task_handler = task_handler

    def push_snapshot(self, snapshot: EventSnapshot):
        snapshot.complete()
        task = self.task_handler.submit_task(self._push_task, snapshot)
        task.add_done_callback(lambda _: logging.debug("Completed uploading snapshot %s", snapshot_id_as_hex_str(snapshot.id)))

    def _push_task(self, snapshot):
        from deep.push import convert_snapshot
        converted = convert_snapshot(snapshot)
        logging.debug("Uploading snapshot: %s", snapshot_id_as_hex_str(snapshot.id))

        stub = SnapshotServiceStub(self.grpc.channel)

        stub.send(converted, metadata=self.grpc.metadata())
