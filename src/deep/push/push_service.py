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

"""Provide service for pushing events to Deep services."""

from deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc import SnapshotServiceStub

from deep import logging
from deep.api.tracepoint import EventSnapshot
from deep.utils import snapshot_id_as_hex_str


class PushService:
    """This service deals with pushing the snapshots to the service endpoints."""

    def __init__(self, config, grpc, task_handler):
        """
        Create a service to handle push events.

        :param config: the current deep config
        :param grpc: the grpc service to use to send events
        :param task_handler: the task handler to offload tasks to
        """
        self.config = config
        self.grpc = grpc
        self.task_handler = task_handler

    def push_snapshot(self, snapshot: EventSnapshot):
        """Push a snapshot to the deep services."""
        self.__decorate(snapshot)
        task = self.task_handler.submit_task(self._push_task, snapshot)
        task.add_done_callback(
            lambda _: logging.debug("Completed uploading snapshot %s", snapshot_id_as_hex_str(snapshot.id)))

    def _push_task(self, snapshot):
        from deep.push import convert_snapshot
        converted = convert_snapshot(snapshot)
        if converted is None:
            return

        logging.debug("Uploading snapshot: %s", snapshot_id_as_hex_str(snapshot.id))

        stub = SnapshotServiceStub(self.grpc.channel)

        stub.send(converted, metadata=self.grpc.metadata())

    def __decorate(self, snapshot):
        plugins = self.config.plugins
        for plugin in plugins:
            try:
                attributes = plugin.collect_attributes()
                if attributes is not None:
                    snapshot.attributes.merge_in(attributes)
            except Exception:
                logging.exception("Error processing plugin %s", plugin.name)
        snapshot.complete()
