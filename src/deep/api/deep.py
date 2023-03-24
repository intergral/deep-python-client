from deep.api.resource import Resource
from deep.grpc import GRPCService
from deep.poll import LongPoll


class Deep:

    def __init__(self, config):
        self.config = config
        self.grpc = GRPCService(self.config)
        self.poll = LongPoll(self.config, self.grpc)

    def start(self):
        self.config.resource = Resource.create()
        self.grpc.start()
        self.poll.start()

