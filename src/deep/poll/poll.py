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
Long poll service for maintaining tracepoint config.

Deep needs to maintain a config of the tracepoints configured by the users. The clients do this by
 periodically polling the long poll service.
"""

# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollRequest, ResponseType
from deepproto.proto.poll.v1.poll_pb2_grpc import PollConfigStub

from deep import logging
from deep.config import ConfigService
from deep.grpc import convert_resource, convert_response, GRPCService
from deep.utils import time_ns, RepeatedTimer


class LongPoll(object):
    """This service deals with polling the remote service to get the tracepoint configs."""

    def __init__(self, config: ConfigService, grpc: GRPCService):
        """
        Create a new long poll service.

        :param config: the deep config service
        :param grpc: the grpc service being used
        """
        self.config = config
        self.grpc = grpc
        self.timer = None

    def start(self):
        """Start the long poll service."""
        logging.info("Starting Long Poll system")
        self.timer = RepeatedTimer("Tracepoint Long Poll", self.config.POLL_TIMER, self.poll)
        self.__initial_poll()
        self.timer.start()

    def __initial_poll(self):
        try:
            self.poll()
        except Exception:
            logging.exception("Initial poll failed. Will continue with interval.")

    def poll(self):
        """Check with the Deep servers for changes to the tracepoint config."""
        stub = PollConfigStub(self.grpc.channel)
        request = PollRequest(ts_nanos=time_ns(), current_hash=self.config.tracepoints.current_hash,
                              resource=convert_resource(self.config.resource))
        response = stub.poll(request, metadata=self.grpc.metadata())

        if response.response_type == ResponseType.NO_CHANGE:
            logging.debug("No Change in config.")
            self.config.tracepoints.update_no_change(response.ts_nanos)
        else:
            self.config.tracepoints.update_new_config(response.ts_nanos, response.current_hash,
                                                      convert_response(response.response))

    def shutdown(self):
        """Shutdown the timer."""
        if self.timer:
            self.timer.stop()
        self.timer = None
