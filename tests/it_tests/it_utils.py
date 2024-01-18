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

"""Provide GRPC services to use in IT tests."""

import uuid
from concurrent import futures
from threading import Thread, Condition

import deepproto
import grpc
# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollResponse, ResponseType
from deepproto.proto.poll.v1.poll_pb2_grpc import PollConfigServicer
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import TracePointConfig, SnapshotResponse
from deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc import SnapshotServiceServicer


def start_server() -> 'MockServer':
    """Create a new MockServer."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    return MockServer(server)


class MockServer:
    """Create a GRPC service that we can connect to during IT tests."""

    def __init__(self, server):
        """Create a new MockServer."""
        self.__thread = None
        self.__poll_service = PollServicer()
        self.__snapshot_service = SnapshotServicer()
        self.__server = server

    def __enter__(self):
        """Start server in thread when 'with' statement starts."""
        deepproto.proto.poll.v1.poll_pb2_grpc.add_PollConfigServicer_to_server(
            self.__poll_service, self.__server)
        deepproto.proto.tracepoint.v1.tracepoint_pb2_grpc.add_SnapshotServiceServicer_to_server(self.__snapshot_service,
                                                                                                self.__server)
        self.__server.add_insecure_port('[::]:43315')
        self.__server.start()
        self.__thread = Thread(target=self.__await)
        self.__thread.start()
        return self

    def __await(self):
        self.__server.wait_for_termination()

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Stop and shutdown GRPC service when 'with' statement completes."""
        self.__server.stop(10)
        self.__thread.join()

    def config(self, custom=None):
        """Get the config for deep to connect to this service."""
        if custom is None:
            custom = {}
        custom['SERVICE_URL'] = "127.0.0.1:43315"
        custom['SERVICE_SECURE'] = 'False'
        return custom

    @property
    def snapshot(self):
        """Get the last received snapshot."""
        return self.__snapshot_service.snapshot

    def add_tp(self, path, line, args=None, watches=None, metrics=None):
        """Add a new Tracepoint to the next poll."""
        if metrics is None:
            metrics = []
        if watches is None:
            watches = []
        if args is None:
            args = {}
        self.__poll_service.tps.append(TracePointConfig(ID=str(uuid.uuid4()),
                                                        path=path,
                                                        line_number=line,
                                                        args=args,
                                                        watches=watches,
                                                        metrics=metrics))
        self.__poll_service.hash = str(uuid.uuid4())

    def await_poll(self):
        """Await for the next poll to be received. Time out after 10 seconds."""
        with self.__poll_service.condition:
            self.__poll_service.condition.wait(10)

    def await_snapshot(self, timeout=10):
        """Await for the next snapshot to be received. Time out after 10 seconds."""
        with self.__snapshot_service.condition:
            self.__snapshot_service.condition.wait(timeout)
        return self.__snapshot_service.snapshot


class PollServicer(PollConfigServicer):
    """Class for handling poll requests during IT tests."""

    def __init__(self):
        """Create a new service."""
        self.__tps = []
        self.__hash = str(uuid.uuid4())
        self.__condition = Condition()

    def poll(self, request, context):
        """Handle a poll request."""
        try:
            return PollResponse(ts_nanos=request.ts_nanos, current_hash=self.__hash, response=self.__tps,
                                response_type=ResponseType.NO_CHANGE if request.current_hash == self.__hash
                                else ResponseType.UPDATE)
        finally:
            with self.__condition:
                self.__condition.notify_all()

    @property
    def condition(self):
        """Get the condition used to control this service."""
        return self.__condition

    @property
    def tps(self):
        """The current config."""
        return self.__tps

    @tps.setter
    def tps(self, value):
        """Update current config."""
        self.__tps = value

    @property
    def hash(self):
        """The current config hash."""
        return self.__hash

    @hash.setter
    def hash(self, value):
        """Update current config hash."""
        self.__hash = value


class SnapshotServicer(SnapshotServiceServicer):
    """Class for handling snapshots during IT tests."""

    def __init__(self):
        """Create a new service."""
        self.__snapshot = None
        self.__condition = Condition()

    def send(self, request, context):
        """Handle a snapshot send event."""
        if request.ByteSize() == 0:
            return SnapshotResponse()
        self.__snapshot = request
        with self.__condition:
            self.__condition.notify_all()
        return SnapshotResponse()

    @property
    def snapshot(self):
        """Get the last received snapshot."""
        return self.__snapshot

    @property
    def condition(self):
        """Get the condition used to control this service."""
        return self.__condition
