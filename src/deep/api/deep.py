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

from deep.api.resource import Resource
from deep.grpc import GRPCService
from deep.poll import LongPoll
from deep.processor import TriggerHandler
from deep.push import PushService
from deep.task import TaskHandler


class Deep:
    """
    This type acts as the main service for DEEP. It will initialise the other services and bind then together.
    DEEP is so small there is no need for service injection work.
    """

    def __init__(self, config):
        self.config = config
        self.grpc = GRPCService(self.config)
        self.task_handler = TaskHandler()
        self.config.set_task_handler(self.task_handler)
        self.poll = LongPoll(self.config, self.grpc)
        self.push = PushService(self.config, self.grpc, self.task_handler)
        self.trigger_handler = TriggerHandler(config, self.push)

    def start(self):
        self.config.resource = Resource.create()
        self.trigger_handler.start()
        self.grpc.start()
        self.poll.start()
