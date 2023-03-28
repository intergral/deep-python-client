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

import grpc

from deep import logging
from deep.api.auth import AuthProvider


class GRPCService:
    def __init__(self, config):
        self.channel = None
        self._config = config
        self._service_url = config.SERVICE_URL
        self._secure = config.SERVICE_SECURE
        self._metadata = None

    def start(self):
        if self._secure:
            logging.info("Connecting securely")
            logging.debug("Connecting securely to: %s", self._service_url)
            self.channel = grpc.secure_channel(self._service_url, grpc.ssl_channel_credentials())
        else:
            logging.info("Connecting with insecure channel")
            logging.debug("Connecting with insecure channel to: %s ", self._service_url)
            self.channel = grpc.insecure_channel(self._service_url)

    def metadata(self):
        if self._metadata is None:
            self._metadata = self._build_metadata()
        return self._metadata

    def _build_metadata(self):
        provider = AuthProvider.get_provider(self._config)
        if provider is not None:
            return provider.provide()
        return []
