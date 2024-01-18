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

from deep import start
from deep.api import Deep


class DeepTest(unittest.TestCase):

    def test_deep(self):
        # do not actual try and start deep in this test
        Deep.start = lambda s: None
        deep = start()
        self.assertTrue(deep.config.APP_ROOT.endswith("/tests"))

    def test_deep_custom_config(self):
        # do not actual try and start deep in this test
        Deep.start = lambda s: None
        deep = start({
            'value': 'something'
        })
        self.assertEqual(deep.config.value, 'something')

    def test_deep_use_configured_app_root(self):
        # do not actual try and start deep in this test
        Deep.start = lambda s: None
        deep = start({
            'APP_ROOT': '/some/path'
        })
        self.assertEqual(deep.config.APP_ROOT, '/some/path')
