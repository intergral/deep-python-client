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
import unittest

from deep.api.auth import AuthProvider
from deep.config import ConfigService


class TestAuth(unittest.TestCase):

    def test_load_auth_none(self):
        config = ConfigService({})
        provider = AuthProvider.get_provider(config)

        self.assertIsNone(provider)

    def test_load_auth_basic(self):
        config = ConfigService({
            'SERVICE_AUTH_PROVIDER': 'deep.api.auth.BasicAuthProvider',
        })
        provider = AuthProvider.get_provider(config)

        self.assertIsNotNone(provider)

        self.assertEqual([], provider.provide())

    def test_load_auth_basic_with_user(self):
        config = ConfigService({
            'SERVICE_AUTH_PROVIDER': 'deep.api.auth.BasicAuthProvider',
            'SERVICE_USERNAME': 'bob',
            'SERVICE_PASSWORD': 'obo'
        })
        provider = AuthProvider.get_provider(config)

        self.assertIsNotNone(provider)

        self.assertEqual([('authorization', 'Basic%20Ym9iOm9ibw==')], provider.provide())
