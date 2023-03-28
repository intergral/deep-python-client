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
        items_ = os.environ.get('PATH')
        service = ConfigService({})
        self.assertEqual(service.PATH, items_)