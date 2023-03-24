# noinspection PyUnresolvedReferences
from deepproto.proto.poll.v1.poll_pb2 import PollRequest, ResponseType
from deepproto.proto.poll.v1.poll_pb2_grpc import PollConfigStub

from deep import logging
from deep.config import Config
from deep.grpc import convert_resource, convert_response
from deep.utils import time_ms, RepeatedTimer


class LongPoll(object):
    config: Config

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
        except:
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
        print(str(self.config.tracepoints.current_config))
