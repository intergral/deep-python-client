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

from parameterized import parameterized

from deep.api.tracepoint import VariableId, Variable
from deep.processor.bfs import Node, NodeValue
from deep.processor.frame_config import FrameProcessorConfig
from deep.processor.variable_processor import var_modifiers, variable_to_string, process_variable, Collector, \
    truncate_string, process_child_nodes


class TestVariable(Variable):
    """
    We do not want to test the hash as this is the memory address so hard to verify in the tests
    """

    def __eq__(self, o: object) -> bool:

        if type(o) != Variable:
            return False

        if id(o) == id(self):
            return True

        return o._type == self._type and o._value == self._value \
            and o._children == self._children and o._truncated == self._truncated


class TestNode(Node):

    def __eq__(self, o: object) -> bool:
        return o.value == self.value


class TestNodeValue(NodeValue):

    def __eq__(self, o: object) -> bool:
        return o.name == self.name and o.value == self.value


class MockCollector(Collector):
    def __init__(self):
        self._var_cache = {}
        self._var_lookup = {}
        self._config = FrameProcessorConfig()
        self._config.close()

    @property
    def var_cache(self):
        return self._var_cache

    @property
    def var_lookup(self):
        return self._var_lookup

    @property
    def frame_config(self) -> FrameProcessorConfig:
        return self._config

    def add_child_to_lookup(self, variable_id, child):
        self._var_lookup[variable_id].children.append(child)

    def check_id(self, identity_hash_id):
        if identity_hash_id in self._var_cache:
            return self._var_cache[identity_hash_id]
        return None

    def new_var_id(self, identity_hash_id: str) -> str:
        var_count = len(self._var_cache)
        new_id = str(var_count + 1)
        self._var_cache[identity_hash_id] = new_id
        return new_id

    def append_variable(self, var_id, variable):
        self._var_lookup[var_id] = variable


class TestVariableProcessor(unittest.TestCase):
    def test_var_modifiers(self):
        self.assertEqual(var_modifiers("some_variable"), [])
        self.assertEqual(var_modifiers("_some_variable"), ['protected'])
        self.assertEqual(var_modifiers("__some_variable"), ['private'])

    @parameterized.expand([
        ["string", "some string", "some string"],
        ["int", 123, "123"],
        ["float", 1.23, "1.23"],
        ["bool", True, "True"],
        ["tuple", ("one", 2), "Size: 2"],
        ["list", ["one", 2], "Size: 2"],
        ["set", {"one", 2}, "Size: 2"],
        ["frozen", frozenset({"one", 2}), "Size: 2"],
        ["list_iter", iter(["one", 2]), "Object of type: <class 'list_iterator'>"],
        ["list_reverse_iter", reversed([1, 2, 3]), "Object of type: <class 'list_reverseiterator'>"]
    ])
    def test_variable_to_string(self, name, _input, expected):
        self.assertEqual(variable_to_string(type(_input), _input), expected)

    @parameterized.expand([
        ["string", "some string", VariableId('1', "string"), True,
         TestVariable('str', "some string", "139916521692464", [], False)],
        ["int", 123, VariableId('1', "int"), True, TestVariable('int', "123", "", [], False)],

        ["float", 1.23, VariableId('1', "float"), True, TestVariable('float', "1.23", "", [], False)],
        ["bool", True, VariableId('1', "bool"), True, TestVariable('bool', "True", "", [], False)],
        ["tuple", ("one", 2), VariableId('1', "tuple"), True, TestVariable('tuple', "Size: 2", "", [], False)],
        ["list", ["one", 2], VariableId('1', "list"), True, TestVariable('list', "Size: 2", "", [], False)],
        ["set", {"one", 2}, VariableId('1', "set"), True, TestVariable('set', "Size: 2", "", [], False)],
        ["frozen", frozenset({"one", 2}), VariableId('1', "frozen"), True,
         TestVariable('frozenset', "Size: 2", "", [], False)],
        ["list_iter", iter(["one", 2]), VariableId('1', "list_iter"), True,
         TestVariable('list_iterator', "Object of type: <class 'list_iterator'>", "", [], False)],
        ["list_reverse_iter", reversed([1, 2, 3]), VariableId('1', "list_reverse_iter"), True,
         TestVariable('list_reverseiterator', "Object of type: <class 'list_reverseiterator'>", "", [], False)],
    ])
    def test_process_variable(self, name, _input, expected_var_id: VariableId, expected_process_children, expected_var):
        collector = MockCollector()
        variable_response = process_variable(collector, name, _input)
        self.assertEqual(variable_response.variable_id, expected_var_id)
        self.assertEqual(variable_response.process_children, expected_process_children)
        self.assertEqual(collector.var_lookup[expected_var_id.vid], expected_var)

    @parameterized.expand([
        [1, "some string", 5, "some ", True],
        [2, "some string", 50, "some string", False],
        [3, "some string", 11, "some string", False],
    ])
    def test_truncate_string(self, name, string, length, expected_value, expected_truncated):
        self.assertEqual(truncate_string(string, length), (expected_value, expected_truncated))

    @parameterized.expand([
        ["string", "some string", 0, []],
        ["int", 123, 0, []],
        ["float", 1.23, 0, []],
        ["bool", False, 0, []],
        ["tuple", ("some", "val"), 0, [TestNode(value=TestNodeValue(name="0", value="some")), TestNode(value=TestNodeValue(name="1", value="val"))]],
        ["list", ["some", "val"], 0, [TestNode(value=TestNodeValue(name="0", value="some")), TestNode(value=TestNodeValue(name="1", value="val"))]],
        ["set", {"some"}, 0, [TestNode(value=TestNodeValue(name="0", value="some"))]],
        ["frozen", frozenset({"some"}), 0, [TestNode(value=TestNodeValue(name="0", value="some"))]],
        ["dict", {"some": "val"}, 0, [TestNode(value=TestNodeValue(name="some", value="val"))]],
        [3, "some string", 6, []],
    ])
    def test_process_child_nodes(self, name, in_var, in_depth, expected):
        collector = MockCollector()
        nodes = process_child_nodes(collector, "1", in_var, in_depth)
        if nodes != expected:
            print(nodes)
        self.assertEqual(nodes, expected)
