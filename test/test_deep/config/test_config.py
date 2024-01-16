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

import sys
import unittest

from deep.config import IN_APP_INCLUDE, IN_APP_EXCLUDE


class ConfigTest(unittest.TestCase):
    def test_in_app_includes(self):
        include = IN_APP_INCLUDE()
        self.assertEqual(include, [])

    def test_in_app_excludes(self):
        include = IN_APP_EXCLUDE()
        self.assertEqual(include, [sys.exec_prefix])
