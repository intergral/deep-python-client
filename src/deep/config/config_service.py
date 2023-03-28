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
import os
from typing import Any

from deep import logging
from deep.api.resource import Resource
from deep.config.tracepoint_config import TracepointConfigService


class ConfigService:
    """
    This is the main service that handles config for DEEP.
    """

    def __init__(self, custom: dict[str, any]):
        """
        Create a new config object
        :param custom: any custom values that are passed to DEEP
        """
        self.custom = custom
        self._resource = None
        self._tracepoint_config = TracepointConfigService()

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
            if self.custom is not None and name in self.custom:
                attr = self.custom[name]

            # if not in custom then load from 'deep.config'
            if attr is None:
                from deep import config
                has_attr = hasattr(config, name)
                if not has_attr:
                    # attribute is no in 'deep.config', so look in env
                    from_env = os.getenv(name, None)
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
    def tracepoints(self) -> TracepointConfigService:
        return self._tracepoint_config

    def add_listener(self, listener):
        self._tracepoint_config.add_listener(listener)
