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

# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollRequest, ResponseType
from deepproto.proto.poll.v1.poll_pb2_grpc import PollConfigStub

from deep import logging
from deep.config import ConfigService
from deep.grpc import convert_resource, convert_response
from deep.utils import time_ms, RepeatedTimer


class LongPoll(object):
    """
    This service deals with polling the remote service to get the tracepoint configs
    """
    config: ConfigService

    def __init__(self, config, grpc):
        self.config = config
        self.grpc = grpc
        self.timer = None

    def start(self):
        logging.info("Starting Long Poll system")
        if self.timer is not None:
            self.timer.stop()
        self.timer = RepeatedTimer("Tracepoint Long Poll", self.config.POLL_TIMER, self.poll)
        self.initial_poll()
        self.timer.start()

    def initial_poll(self):
        try:
            self.poll()
        except Exception:
            logging.exception("Initial poll failed. Will continue with interval.")

    def poll(self):
        stub = PollConfigStub(self.grpc.channel)
        request = PollRequest(ts=time_ms(), current_hash=self.config.tracepoints.current_hash,
                              resource=convert_resource(self.config.resource))
        response = stub.poll(request, metadata=self.grpc.metadata())

        if response.response_type == ResponseType.NO_CHANGE:
            logging.debug("No Change in config.")
            self.config.tracepoints.update_no_change(response.ts)
        else:
            self.config.tracepoints.update_new_config(response.ts, response.current_hash,
                                                      convert_response(response.response))
