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

from deep.grpc import convert_value, convert_label_expressions
# noinspection PyUnresolvedReferences
from deepproto.proto.tracepoint.v1.tracepoint_pb2 import LabelExpression


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

    def test_convert_label_expression(self):
        expression = LabelExpression(key="test", expression="a thing")
        value = convert_label_expressions([expression])
        self.assertEqual("test", value[0].key)
        self.assertEqual("a thing", value[0].expression)

    def test_convert_label_static(self):
        expression = LabelExpression(key="test", static=convert_value("a string"))
        value = convert_label_expressions([expression])
        self.assertEqual("test", value[0].key)
        self.assertEqual("a string", value[0].static)
