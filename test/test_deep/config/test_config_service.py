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

import os
import unittest

from deep.config import ConfigService


class TestConfigService(unittest.TestCase):
    def test_custom_attr(self):
        service = ConfigService({'SOME_VALUE': 'thing'})
        self.assertEqual(service.SOME_VALUE, 'thing')

    def test_custom_attr_callable(self):
        service = ConfigService({'SOME_VALUE': lambda: 'thing'})
        self.assertEqual(service.SOME_VALUE, 'thing')

    def test_env_attr(self):
        items_ = os.environ.setdefault("DEEP_PATH", "a thing")
        service = ConfigService({})
        self.assertEqual(service.PATH, items_)
