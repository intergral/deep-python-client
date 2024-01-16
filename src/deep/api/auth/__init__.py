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

"""Services for customizing auth connection."""

import abc
import base64
from importlib import import_module
from typing import Optional

from deep.config import ConfigService


class UnknownAuthProvider(Exception):
    """This exception is thrown when the configured auth provider cannot be loaded."""

    pass


class AuthProvider(abc.ABC):
    """
    This is the abstract class to define an AuthProvider.

    The 'provide' function will be called when the system needs to get an auth token.
    """

    def __init__(self, config: ConfigService) -> None:
        """
        Create a new auth provider.

        :param config: the deep config service
        """
        self._config = config

    @staticmethod
    def get_provider(config: ConfigService) -> Optional['AuthProvider']:
        """
        Get the provider to use.

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
        Provide the auth metadata.

        This is called when we need to get the auth for the request.

        :return: a list of tuples to be attached to the outbound request
        """
        raise NotImplementedError()


class BasicAuthProvider(AuthProvider):
    """This is a provider for http basic auth. This expects the config to provide a username and password."""

    def provide(self):
        """
        Provide the auth metadata.

        This is called when we need to get the auth for the request.

        :return: a list of tuples to be attached to the outbound request
        """
        username = self._config.SERVICE_USERNAME
        password = self._config.SERVICE_PASSWORD
        if username is not None and password is not None:
            encode = base64.b64encode(
                (username + ':' + password).encode("utf-8"))
            return [('authorization', 'Basic%20' + encode.decode('utf-8'))]
        return []
