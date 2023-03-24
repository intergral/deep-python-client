from deep.api.resource import Resource
from deep.grpc import GRPCService
from deep.poll import LongPoll
from deep.push import PushService
from deep.task import TaskHandler


class Deep:

    def __init__(self, config):
        self.config = config
        self.grpc = GRPCService(self.config)
        self.task_handler = TaskHandler()
        self.config.set_task_handler(self.task_handler)
        self.poll = LongPoll(self.config, self.grpc)
        self.push = PushService(self.config, self.grpc, self.task_handler)

    def start(self):
        self.config.resource = Resource.create()
        self.grpc.start()
        self.poll.start()
