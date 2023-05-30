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

from deep.api.plugin import load_plugins
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
        self.started = False
        self.config = config
        self.grpc = GRPCService(self.config)
        self.task_handler = TaskHandler()
        self.config.set_task_handler(self.task_handler)
        self.poll = LongPoll(self.config, self.grpc)
        self.push = PushService(self.config, self.grpc, self.task_handler)
        self.trigger_handler = TriggerHandler(config, self.push)

    def start(self):
        if self.started:
            return
        plugins, attributes = load_plugins()
        self.config.plugins = plugins
        self.config.resource = Resource.create(attributes)
        self.trigger_handler.start()
        self.grpc.start()
        self.poll.start()
        self.started = True

    def shutdown(self):
        if not self.started:
            return
        self.task_handler.flush()
        self.started = False
