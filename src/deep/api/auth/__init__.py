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

import abc
import base64
from importlib import import_module
from typing import Optional

from deep.config import ConfigService


class UnknownAuthProvider(Exception):
    """This exception is thrown when the configured auth provider cannot be loaded"""
    pass


class AuthProvider(abc.ABC):
    """
    This is the abstract class to define an AuthProvider. The 'provide' function will be called
    when the system needs to get an auth token.
    """

    def __init__(self, config) -> None:
        self._config = config

    @staticmethod
    def get_provider(config: ConfigService) -> Optional['AuthProvider']:
        """
        Static function to load the correct auth provider based on the current config.
        :param config: The agent config
        :return: the loaded provider
        :raises: UnknownAuthProvider if we cannot load the provider configured
        """
        provider = config.SERVICE_AUTH_PROVIDER
        if provider is None or provider == "":
            return None

        module, cls = provider.rsplit(".", 1)
        provider_class = getattr(import_module(module), cls)
        if provider_class is None:
            raise UnknownAuthProvider("Cannot find auth provider with name: %s" % provider)

        return provider_class(config)

    @abc.abstractmethod
    def provide(self):
        """
        This is called when we need to get the auth for the request.
        :return: a list of tuples to be attached to the outbound request
        """
        raise NotImplementedError()


class BasicAuthProvider(AuthProvider):
    """
    This is a provider for http basic auth. This expects the config to provide a username and password.
    """
    def provide(self):
        username = self._config.SERVICE_USERNAME
        password = self._config.SERVICE_PASSWORD
        if username is not None and password is not None:
            encode = base64.b64encode(
                (username + ':' + password).encode("utf-8"))
            return [('authorization', 'Basic%20' + encode.decode('utf-8'))]
        return []
