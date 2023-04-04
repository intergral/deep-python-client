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