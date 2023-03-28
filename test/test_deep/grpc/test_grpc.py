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

from deep.grpc import convert_value


class GRPCPackage(unittest.TestCase):

    def test_convert_string(self):
        value = convert_value("some string")
        self.assertEqual(value.string_value, "some string")
        self.assertEqual(value.bool_value, False)
        self.assertEqual(value.int_value, 0)
        self.assertEqual(value.double_value, 0)
        self.assertEqual(value.bytes_value, b'')

    def test_convert_bool(self):
        value = convert_value(True)
        self.assertEqual(value.string_value, "")
        self.assertEqual(value.bool_value, True)
        self.assertEqual(value.int_value, 0)
        self.assertEqual(value.double_value, 0)
        self.assertEqual(value.bytes_value, b'')

    def test_convert_int(self):
        value = convert_value(int(1))
        self.assertEqual(value.string_value, "")
        self.assertEqual(value.bool_value, False)
        self.assertEqual(value.int_value, 1)
        self.assertEqual(value.double_value, 0)
        self.assertEqual(value.bytes_value, b'')

    def test_convert_double(self):
        value = convert_value(float(2))
        self.assertEqual(value.string_value, "")
        self.assertEqual(value.bool_value, False)
        self.assertEqual(value.int_value, 0)
        self.assertEqual(value.double_value, 2)
        self.assertEqual(value.bytes_value, b'')

    def test_convert_bytes(self):
        value = convert_value(b"some string")
        self.assertEqual(value.string_value, "")
        self.assertEqual(value.bool_value, False)
        self.assertEqual(value.int_value, 0)
        self.assertEqual(value.double_value, 0)
        self.assertEqual(value.bytes_value, b'some string')

    def test_convert_array(self):
        value = convert_value(["some string"])
        self.assertEqual(value.array_value.values[0].string_value, "some string")

    def test_convert_dict(self):
        value = convert_value({'some': 'string'})
        self.assertEqual(value.kvlist_value.values[0].key, "some")
        self.assertEqual(value.kvlist_value.values[0].value.string_value, "string")
