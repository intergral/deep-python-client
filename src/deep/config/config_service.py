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

import os
from typing import Any, List, Dict, Tuple, Optional

from deep import logging
from deep.api.plugin import Plugin
from deep.api.resource import Resource
from deep.config.tracepoint_config import TracepointConfigService, ConfigUpdateListener
from deep.logging.tracepoint_logger import DefaultLogger, TracepointLogger


class ConfigService:
    """
    This is the main service that handles config for DEEP.
    """

    def __init__(self, custom: Dict[str, any]):
        """
        Create a new config object
        :param custom: any custom values that are passed to DEEP
        """
        self._plugins = []
        self.__custom = custom
        self._resource = None
        self._tracepoint_config = TracepointConfigService()
        self._tracepoint_logger: 'TracepointLogger' = DefaultLogger(self)

    def __getattribute__(self, name: str) -> Any:
        """
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
        super().__setattr__(name, value)

    def set_task_handler(self, task_handler):
        self._tracepoint_config.set_task_handler(task_handler)

    @property
    def resource(self) -> Resource:
        return self._resource

    @resource.setter
    def resource(self, new_resource):
        self._resource = new_resource

    @property
    def plugins(self) -> List[Plugin]:
        return self._plugins

    @plugins.setter
    def plugins(self, plugins):
        self._plugins = plugins

    @property
    def tracepoints(self) -> 'TracepointConfigService':
        return self._tracepoint_config

    def add_listener(self, listener: 'ConfigUpdateListener'):
        self._tracepoint_config.add_listener(listener)

    @property
    def tracepoint_logger(self) -> 'TracepointLogger':
        return self._tracepoint_logger

    @tracepoint_logger.setter
    def tracepoint_logger(self, logger: 'TracepointLogger'):
        self._tracepoint_logger = logger

    def log_tracepoint(self, log_msg: str, tp_id: str, snap_id: str):
        self._tracepoint_logger.log_tracepoint(log_msg, tp_id, snap_id)

    def is_app_frame(self, filename: str) -> Tuple[bool, Optional[str]]:
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
