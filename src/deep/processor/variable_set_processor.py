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
from typing import Tuple

from deep.processor.bfs import ParentNode, Node, NodeValue, breadth_first_search
from deep.processor.variable_processor import truncate_string, variable_to_string, process_variable, \
    process_child_nodes, Collector

from deep.api.tracepoint import Variable, VariableId


class VariableCacheProvider:
    __cache: dict[str, str]

    def __init__(self):
        self.__cache = {}

    def check_id(self, identity_hash_id):
        if identity_hash_id in self.__cache:
            return self.__cache[identity_hash_id]
        return None

    @property
    def size(self):
        return len(self.__cache)

    def new_var_id(self, identity_hash_id):
        var_count = self.size
        new_id = str(var_count + 1)
        self.__cache[identity_hash_id] = new_id
        return new_id


class VariableProcessorConfig:
    DEFAULT_MAX_VAR_DEPTH = 5
    DEFAULT_MAX_VARIABLES = 1000
    DEFAULT_MAX_COLLECTION_SIZE = 10
    DEFAULT_MAX_STRING_LENGTH = 1024
    DEFAULT_MAX_WATCH_VARS = 100

    def __init__(self, max_string_length=DEFAULT_MAX_STRING_LENGTH, max_variables=DEFAULT_MAX_VARIABLES,
                 max_collection_size=DEFAULT_MAX_COLLECTION_SIZE, max_var_depth=DEFAULT_MAX_VAR_DEPTH):
        self.max_var_depth = max_var_depth
        self.max_collection_size = max_collection_size
        self.max_variables = max_variables
        self.max_string_length = max_string_length


class VariableSetProcessor(Collector):

    def __init__(self, var_lookup: dict[str, 'Variable'], var_cache: VariableCacheProvider,
                 config: VariableProcessorConfig = VariableProcessorConfig()):
        self.__var_lookup = var_lookup
        self.__var_cache = var_cache
        self.__config = config

    def process_variable(self, name: str, value: any) -> Tuple[VariableId, str]:
        identity_hash_id = str(id(value))
        check_id = self.__var_cache.check_id(identity_hash_id)
        if check_id is not None:
            # this means the watch result is already in the var_lookup
            return VariableId(check_id, name), str(value)

        # else this is an unknown value so process breadth first
        var_ids = []

        class FrameParent(ParentNode):

            def add_child(self, child):
                var_ids.append(child)

        root_parent = FrameParent()

        initial_nodes = [Node(NodeValue(name, value), parent=root_parent)]
        breadth_first_search(Node(None, initial_nodes, root_parent), self.search_function)

        var_id = self.__var_cache.check_id(identity_hash_id)

        return VariableId(var_id, name), str(value)

    def search_function(self, node: Node) -> bool:
        """
        This is the search function to use during BFS
        :param node: the current node we are process
        :return: True, if we want to continue with the nodes children
        """
        if not self.check_var_count():
            # we have exceeded the var count, so do not continue
            return False

        node_value = node.value
        if node_value is None:
            # this node has no value, continue with children
            return True

        # process this node variable
        process_result = process_variable(self, node_value)
        var_id = process_result.variable_id
        # add the result to the parent - this maintains the hierarchy in the var look up
        node.parent.add_child(var_id)

        # some variables do not want the children processed (e.g. strings)
        if process_result.process_children:
            # process children and add to node
            child_nodes = process_child_nodes(self, var_id.vid, node_value.value, node.depth)
            node.add_children(child_nodes)
        return True

    def check_var_count(self):
        if self.__var_cache.size > self.__config.max_variables:
            return False
        return True

    @property
    def var_lookup(self):
        return self.__var_lookup

    @property
    def max_string_length(self) -> int:
        return self.__config.max_string_length

    @property
    def max_collection_size(self) -> int:
        return self.__config.max_collection_size

    @property
    def max_var_depth(self) -> int:
        return self.__config.max_var_depth

    def append_child(self, variable_id, child):
        self.__var_lookup[variable_id].children.append(child)

    def check_id(self, identity_hash_id: str) -> str:
        return self.__var_cache.check_id(identity_hash_id)

    def new_var_id(self, identity_hash_id: str) -> str:
        return self.__var_cache.new_var_id(identity_hash_id)

    def append_variable(self, var_id, variable):
        self.__var_lookup[var_id] = variable
