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

from deep.api.plugin.python import PythonPlugin


class TestPython(unittest.TestCase):

    def test_load_plugin(self):
        plugin = PythonPlugin()
        load_plugin = plugin.resource()
        self.assertIsNotNone(load_plugin)
        self.assertIsNotNone(load_plugin.attributes.get('python_version'))

    def test_collect_attributes(self):
        plugin = PythonPlugin()
        attributes = plugin.decorate(None)
        self.assertIsNotNone(attributes)
        self.assertEqual("MainThread", attributes.get("thread_name"))
