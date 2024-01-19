#       Copyright (C) 2024  Intergral GmbH
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

import deep
from deep.api.plugin import load_plugins, Plugin
from deep.config import ConfigService


class BadPlugin(Plugin):
    def __init__(self):
        super().__init__()

        raise Exception('test: failed load')


class TestPluginLoader(unittest.TestCase):

    def setUp(self):
        deep.logging.init(ConfigService())

    def test_load_plugins(self):
        plugins = load_plugins(None)
        self.assertIsNotNone(plugins)
        self.assertEqual(3, len(plugins))

    def test_handle_bad_plugin(self):
        plugins = load_plugins(None, [BadPlugin.__qualname__])

        self.assertEqual(3, len(plugins))

        plugins = load_plugins(None, [BadPlugin.__module__ + '.' + BadPlugin.__name__])

        self.assertEqual(3, len(plugins))
