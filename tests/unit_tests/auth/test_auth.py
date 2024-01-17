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
