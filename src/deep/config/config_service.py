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

"""Service for handling deep config."""

import os
from typing import Any, List, Dict, Tuple, Optional, Generator

from deep import logging
from deep.api.plugin import Plugin, ResourceProvider, PLUGIN_TYPE, SnapshotDecorator, TracepointLogger
from deep.api.plugin.metric import MetricProcessor
from deep.api.plugin.span import SpanProcessor
from deep.api.resource import Resource
from deep.config.tracepoint_config import TracepointConfigService, ConfigUpdateListener


class ConfigService:
    """This is the main service that handles config for DEEP."""

    def __init__(self, custom: Dict[str, any] = None, tracepoints=TracepointConfigService()):
        """
        Create a new config object.

        :param custom: any custom values that are passed to DEEP
        """
        if custom is None:
            custom = {}
        self._plugins = []
        self.__custom = custom
        self._resource = None
        self._tracepoint_config = tracepoints

    def __getattribute__(self, name: str) -> Any:
        """
        Get attribute from config.

        A custom attribute processor to load the config values

        :param name: the key to load
        :return: the loaded value or None
        """
        attr = None
        try:
            # first we try to load from our selves. This handles things like getting 'self.custom' etc.
            attr = super().__getattribute__(name)
        except AttributeError:
            # if we get here then we are not an attribute on 'self'
            # so look in the custom map
            if self.__custom is not None and name in self.__custom:
                attr = self.__custom[name]

            # if not in custom then load from 'deep.config'
            if attr is None:
                from deep import config
                has_attr = hasattr(config, name)
                if not has_attr:
                    # attribute is no in 'deep.config', so look in env
                    from_env = os.getenv("DEEP_%s" % name, None)
                    if from_env is None:
                        # not found in env - log and return none
                        logging.warning("Unrecognised config key: %s", name)
                        return None
                    else:
                        # if loaded from env, then cannot be function
                        return from_env
                attr = getattr(config, name, None)

            # some can be callable - if is callable call it
            if callable(attr):
                return attr()

        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute on this config."""
        super().__setattr__(name, value)

    def set_task_handler(self, task_handler):
        """
        Set the task handler to use.

        :param task_handler: the taskhandler
        """
        self._tracepoint_config.set_task_handler(task_handler)

    @property
    def resource(self) -> Resource:
        """Get the resource that describes this client."""
        return self._resource

    @resource.setter
    def resource(self, new_resource):
        """Set the resource that describes this client."""
        self._resource = new_resource

    @property
    def plugins(self) -> List[Plugin]:
        """Get the active deep client plugins."""
        return self._plugins

    @plugins.setter
    def plugins(self, plugins):
        """Set the active deep client plugins."""
        self._plugins = plugins

    @property
    def tracepoints(self) -> 'TracepointConfigService':
        """The tracepoint config service."""
        return self._tracepoint_config

    def add_listener(self, listener: 'ConfigUpdateListener'):
        """
        Add a new listener to the config.

        :param listener: the listener to add
        """
        self._tracepoint_config.add_listener(listener)

    @property
    def tracepoint_logger(self) -> TracepointLogger:
        """Get the tracepoint logger."""
        return self._find_plugin(TracepointLogger)

    @property
    def resource_providers(self) -> Generator[ResourceProvider, None, None]:
        """Generator for available resource providers."""
        return self.__plugin_generator(ResourceProvider)

    @property
    def snapshot_decorators(self) -> Generator[SnapshotDecorator, None, None]:
        """Generator for snapshot decorators."""
        return self.__plugin_generator(SnapshotDecorator)

    @property
    def metric_processors(self) -> Generator[MetricProcessor, None, None]:
        """Generator for snapshot decorators."""
        return self.__plugin_generator(MetricProcessor)

    @property
    def has_metric_processor(self) -> bool:
        """Is there a configured metric processor."""
        return self._find_plugin(MetricProcessor) is not None

    @property
    def span_processors(self) -> Generator[SpanProcessor, None, None]:
        """Generator for snapshot decorators."""
        return self.__plugin_generator(SpanProcessor)

    @property
    def has_span_processor(self) -> bool:
        """Is there a configured metric processor."""
        return self._find_plugin(SpanProcessor) is not None

    def is_app_frame(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the current frame is a user application frame.

        :param filename: the frame file name
        :return: True if add frame, else False
        """
        in_app_include = self.IN_APP_INCLUDE
        in_app_exclude = self.IN_APP_EXCLUDE

        for path in in_app_exclude:
            if filename.startswith(path):
                return False, path

        for path in in_app_include:
            if filename.startswith(path):
                return True, path

        if filename.startswith(self.APP_ROOT):
            return True, self.APP_ROOT

        return False, None

    def _find_plugin(self, plugin_type) -> PLUGIN_TYPE:
        return next(self.__plugin_generator(plugin_type), None)

    def _find_plugins(self, plugin_type) -> List[PLUGIN_TYPE]:
        plugins = []
        for plugin in self.__plugin_generator(plugin_type):
            plugins.append(plugin)
        return plugins

    def __plugin_generator(self, plugin_type) -> Generator[PLUGIN_TYPE, None, None]:
        for plugin in self._plugins:
            if isinstance(plugin, plugin_type):
                yield plugin
