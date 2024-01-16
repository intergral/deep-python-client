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

"""Service for connecting to GRPC channel."""

import grpc

from deep import logging
from deep.api.auth import AuthProvider
from deep.config import ConfigService
from deep.utils import str2bool


class GRPCService:
    """This service handles config and initialising the GRPc channel that will be used."""

    def __init__(self, config: ConfigService):
        """
        Create a new grpc service.

        :param config: the deep config
        """
        self.channel = None
        self._config = config
        self._service_url = config.SERVICE_URL
        self._secure = config.SERVICE_SECURE
        self._metadata = None

    def start(self):
        """Start and connect the GRPC channel."""
        if str2bool(self._secure):
            logging.info("Connecting securely")
            logging.debug("Connecting securely to: %s", self._service_url)
            self.channel = grpc.secure_channel(self._service_url, grpc.ssl_channel_credentials())
        else:
            logging.info("Connecting with insecure channel")
            logging.debug("Connecting with insecure channel to: %s ", self._service_url)
            self.channel = grpc.insecure_channel(self._service_url)

    def metadata(self):
        """
        Get GRPC metadata.

        Call this to get any metadata that should be attached to calls.

        :return: list of metadata
        """
        if self._metadata is None:
            self._metadata = self._build_metadata()
        return self._metadata

    def _build_metadata(self):
        provider = AuthProvider.get_provider(self._config)
        if provider is not None:
            return provider.provide()
        return []
