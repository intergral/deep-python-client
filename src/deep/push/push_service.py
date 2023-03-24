from deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc import SnapshotServiceStub

from deep import logging
from deep.api.tracepoint import EventSnapshot


class PushService:
    def __init__(self, config, grpc, task_handler):
        self.config = config
        self.grpc = grpc
        self.task_handler = task_handler

    def push_snapshot(self, snapshot: EventSnapshot):
        snapshot.complete()
        task = self.task_handler.submit_task(self._push_task, snapshot)
        task.add_done_callback(lambda _: logging.debug("Completed uploading snapshot %s", snapshot.id))

    def _push_task(self, snapshot):
        from deep.push import convert_snapshot
        converted = convert_snapshot(snapshot)
        logging.debug("Uploading snapshot: %s", snapshot.id)

        stub = SnapshotServiceStub(self.grpc.channel)

        stub.send(converted, metadata=self.grpc.metadata())
