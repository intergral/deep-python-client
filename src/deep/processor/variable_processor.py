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
import abc

from deep import logging
from deep.api.tracepoint import VariableId, Variable
from .bfs import Node, ParentNode, NodeValue
from .frame_config import FrameProcessorConfig

NO_CHILD_TYPES = [
    'str',
    'int',
    'float',
    'bool',
    'type',
    'module',
    'unicode',
    'long'
]

LIST_LIKE_TYPES = [
    'frozenset',
    'set',
    'list',
    'tuple',
]

ITER_LIKE_TYPES = [
    'list_iterator',
    'listiterator',
    'list_reverseiterator',
    'listreverseiterator',
]


class Collector(abc.ABC):

    @property
    @abc.abstractmethod
    def frame_config(self) -> FrameProcessorConfig:
        pass

    @abc.abstractmethod
    def add_child_to_lookup(self, variable_id, child):
        pass

    @abc.abstractmethod
    def check_id(self, identity_hash_id):
        pass

    @abc.abstractmethod
    def new_var_id(self, identity_hash_id):
        pass

    @abc.abstractmethod
    def append_variable(self, var_id, variable):
        pass


class VariableResponse:
    def __init__(self, variable_id, process_children=True):
        self.__variable_id = variable_id
        self.__process_children = process_children

    @property
    def variable_id(self):
        return self.__variable_id

    @property
    def process_children(self):
        return self.__process_children


def var_modifiers(var_name):
    if var_name.startswith("__"):
        return ['private']
    if var_name.startswith("_"):
        return ['protected']
    return []


def variable_to_string(variable_type, var_value):
    if variable_type is int \
            or variable_type is float \
            or variable_type is bool \
            or variable_type.__name__ == 'long' \
            or var_value is None:
        return str(var_value)
    elif variable_type.__name__ in ITER_LIKE_TYPES:
        return 'Object of type: %s' % variable_type
    elif variable_type is dict \
            or variable_type.__name__ in LIST_LIKE_TYPES:
        return 'Size: %s' % len(var_value)
    else:
        return str(var_value)


def process_variable(frame_collector: Collector, var_name: str, var_value: any) -> VariableResponse:
    identity_hash_id = str(id(var_value))
    check_id = frame_collector.check_id(identity_hash_id)
    if check_id is not None:
        return VariableResponse(VariableId(check_id, var_name, var_modifiers(var_name)), process_children=False)

    var_id = frame_collector.new_var_id(identity_hash_id)

    variable_id = VariableId(var_id, var_name, var_modifiers(var_name))
    variable_type = type(var_value)
    variable_value_str, truncated = truncate_string(variable_to_string(variable_type, var_value),
                                                    frame_collector.frame_config.max_string_length)

    variable = Variable(str(variable_type.__name__), variable_value_str, identity_hash_id, [], truncated)

    frame_collector.append_variable(var_id, variable)

    return VariableResponse(variable_id, process_children=True)


def truncate_string(string, max_length):
    return string[:max_length], len(string) > max_length


def process_child_nodes(
        frame_collector: Collector,
        variable_id: str,
        var_value: any,
        frame_depth: int
) -> list[Node]:
    variable_type = type(var_value)
    if variable_type in NO_CHILD_TYPES:
        return []

    if frame_depth + 1 >= frame_collector.frame_config.max_var_depth:
        return []

    class VariableParent(ParentNode):

        def add_child(self, child: VariableId):
            frame_collector.add_child_to_lookup(variable_id, child)

    return find_children_for_parent(frame_collector, VariableParent(), var_value, variable_type)


def find_children_for_parent(frame_collector: Collector, parent_node: ParentNode, value: any,
                             variable_type: type):
    if variable_type is dict:
        return process_dict_breadth_first(parent_node, value)
    elif variable_type.__name__ in LIST_LIKE_TYPES:
        return process_list_breadth_first(frame_collector, parent_node, value)
    elif variable_type.__name__ in ITER_LIKE_TYPES:
        return process_iterable_breadth_first(frame_collector, parent_node, value)
    elif isinstance(value, Exception):
        return process_list_breadth_first(frame_collector, parent_node, value.args)
    elif hasattr(value, '__dict__'):
        return process_dict_breadth_first(parent_node, value.__dict__)
    else:
        logging.debug("Unknown type processed %s", variable_type)
        return []


def process_dict_breadth_first(parent_node, value):
    # we wrap the keys() in a call to list to prevent concurrent changes
    return [Node(value=NodeValue(key, value[key]), parent=parent_node) for key in list(value.keys()) if
            key in value]


def process_list_breadth_first(frame_collector: Collector, parent_node, value):
    nodes = []
    total = 0
    for val_ in tuple(value):
        if total >= frame_collector.frame_config.max_collection_size:
            parent_node.flag('list_truncated')
            break
        nodes.append(Node(value=NodeValue(str(total), val_), parent=parent_node))
        total += 1
    return nodes


# todo this needs to be checked, does it affect the position of the iterable
def process_iterable_breadth_first(frame_collector: Collector, parent_node, value):
    nodes = []
    end = VariableId(-1, 'end')
    val = next(value, end)
    total = 0
    while val is not end:
        if total > frame_collector.frame_config.max_collection_size:
            parent_node.flag('list_truncated')
            break
        nodes.append(Node(value=NodeValue(str(total), val), parent=parent_node))
        val = next(value, end)
        total += 1
    return nodes
