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
