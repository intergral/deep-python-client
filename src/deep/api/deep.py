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
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.from typing import Dict, List

"""The main services for Deep."""
from typing import Dict, List

import deep.logging
from deep.api.plugin import load_plugins
from deep.api.resource import Resource
from deep.api.tracepoint.tracepoint_config import MetricDefinition
from deep.config import ConfigService
from deep.config.tracepoint_config import TracepointConfigService
from deep.grpc import GRPCService
from deep.poll import LongPoll
from deep.processor.trigger_handler import TriggerHandler
from deep.push import PushService
from deep.task import TaskHandler


class Deep:
    """
    The main service for deep.

    This type acts as the main service for DEEP. It will initialise the other services and bind then together.
    DEEP is so small there is no need for service injection work.
    """

    def __init__(self, config: 'ConfigService'):
        """
        Create new deep service.

        :param config: the config to use.
        """
        self.started = False
        self.config = config
        self.grpc = GRPCService(self.config)
        self.task_handler = TaskHandler()
        self.config.set_task_handler(self.task_handler)
        self.poll = LongPoll(self.config, self.grpc)
        self.push = PushService(self.grpc, self.task_handler)
        self.trigger_handler = TriggerHandler(config, self.push)

    def start(self):
        """Start Deep."""
        if self.started:
            return
        self.config.plugins = load_plugins(self.config, self.config.PLUGINS)
        default_resource = Resource.create()
        for provider in self.config.resource_providers:
            try:
                plugin_resource = provider.resource()
                if plugin_resource:
                    default_resource = default_resource.merge(plugin_resource)
            except Exception:
                deep.logging.exception("Failed to process plugin resource {}", provider.name)

        self.config.resource = default_resource
        self.trigger_handler.start()
        self.grpc.start()
        self.poll.start()
        self.started = True

    def shutdown(self):
        """Shutdown deep."""
        if not self.started:
            return
        self.trigger_handler.shutdown()
        self.task_handler.flush()
        self.poll.shutdown()
        for plugin in self.config.plugins:
            plugin.shutdown()
        deep.logging.info("Deep is shutdown.")
        self.started = False

    def register_tracepoint(self, path: str, line: int, args: Dict[str, str] = None,
                            watches: List[str] = None,
                            metrics: List[MetricDefinition] = None) -> 'TracepointRegistration':
        """
        Register a new tracepoint.

        :param path: the source path
        :param line: the line number
        :param args: the args
        :param watches: the watches
        :param metrics: the metrics
        :return: the new registration
        """
        if metrics is None:
            metrics = []
        if watches is None:
            watches = []
        if args is None:
            args = {}
        tp_id = self.config.tracepoints.add_custom(path, line, args, watches, metrics)
        return TracepointRegistration(tp_id, self.config.tracepoints)


class TracepointRegistration:
    """Registration of a new tracepoint."""

    def __init__(self, _id: str, tracepoints: TracepointConfigService):
        """
        Create a new registration.

        :param _id: the created config id
        :param tracepoints: the config service
        """
        self.__id: str = _id
        self.__tpServ: TracepointConfigService = tracepoints

    def unregister(self):
        """Remove this custom tracepoint."""
        self.__tpServ.remove_custom(self.__id)
