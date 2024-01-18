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

"""Handle the processing of variables sets."""

from typing import Tuple, Optional, Dict

from deep.api.tracepoint import Variable, VariableId
from deep.processor.bfs import ParentNode, Node, NodeValue, breadth_first_search
from deep.processor.variable_processor import process_variable, \
    process_child_nodes, Collector


class VariableCacheProvider:
    """
    Variable cache provider.

    Manage the caching of variables for a trigger context.
    """

    __cache: Dict[str, str]

    def __init__(self):
        """Create new cache."""
        self.__cache = {}

    def check_id(self, identity_hash_id) -> Optional[str]:
        """
        Check if id is in the cache.

        :param identity_hash_id: the identity hash to check
        :return: the internal id for this hash, or None if not set
        """
        if identity_hash_id in self.__cache:
            return self.__cache[identity_hash_id]
        return None

    @property
    def size(self):
        """The number of variables we have cached."""
        return len(self.__cache)

    def new_var_id(self, identity_hash_id):
        """
        Create a new variable id from the hash id.

        :param identity_hash_id: the hash id to map the new id to.
        :return: the new id
        """
        var_count = self.size
        new_id = str(var_count + 1)
        self.__cache[identity_hash_id] = new_id
        return new_id


class VariableProcessorConfig:
    """Variable process config."""

    DEFAULT_MAX_VAR_DEPTH = 5
    DEFAULT_MAX_VARIABLES = 1000
    DEFAULT_MAX_COLLECTION_SIZE = 10
    DEFAULT_MAX_STRING_LENGTH = 1024
    DEFAULT_MAX_WATCH_VARS = 100

    def __init__(self, max_string_length=DEFAULT_MAX_STRING_LENGTH, max_variables=DEFAULT_MAX_VARIABLES,
                 max_collection_size=DEFAULT_MAX_COLLECTION_SIZE, max_var_depth=DEFAULT_MAX_VAR_DEPTH):
        """
        Create a new config for the variable processing.

        :param max_string_length: the max length of a string
        :param max_variables: the max number of variables
        :param max_collection_size: the max size of a collection
        :param max_var_depth: the max depth to process
        """
        self.max_var_depth = max_var_depth
        self.max_collection_size = max_collection_size
        self.max_variables = max_variables
        self.max_string_length = max_string_length


class VariableSetProcessor(Collector):
    """Handle the processing of variables."""

    def __init__(self, var_lookup: Dict[str, 'Variable'], var_cache: VariableCacheProvider,
                 config: VariableProcessorConfig = VariableProcessorConfig()):
        """
        Create a new variable set processor.

        :param var_lookup: the var lookup to use
        :param var_cache: the var cache to use
        :param config: the var process config to use
        """
        self.__var_lookup = var_lookup
        self.__var_cache = var_cache
        self.__config = config

    def process_variable(self, name: str, value: any) -> Tuple[VariableId, str]:
        """
        Process a variable name and value.

        :param name: the variable name
        :param value: the variable value
        :return:
        """
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
        Search for child variables using BFS.

        This is the search function to use during BFS.

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
        """Check if we have processed our max set of variables."""
        if self.__var_cache.size > self.__config.max_variables:
            return False
        return True

    @property
    def var_lookup(self):
        """Get var look up."""
        return self.__var_lookup

    @property
    def max_string_length(self) -> int:
        """
        Get the max length of a string.

        :return int: the configured value
        """
        return self.__config.max_string_length

    @property
    def max_collection_size(self) -> int:
        """
        Get the max size of a collection.

        :return int: the configured value
        """
        return self.__config.max_collection_size

    @property
    def max_var_depth(self) -> int:
        """
        Get the max depth to process.

        :return int: the configured value
        """
        return self.__config.max_var_depth

    def append_child(self, variable_id, child):
        """
        Append a chile to existing variable.

        This is called when a child variable has been processed and the result should be attached to a
        variable that has already been processed.

        :param str variable_id: the internal variable id of the parent variable
        :param VariableId child: the internal variable id value to attach to the parent
        """
        self.__var_lookup[variable_id].children.append(child)

    def check_id(self, identity_hash_id: str) -> str:
        """
        Check if the identity_hash_id is known to us, and return the lookup id.

        :param identity_hash_id: the id of the object
        :return: the lookup id used
        """
        return self.__var_cache.check_id(identity_hash_id)

    def new_var_id(self, identity_hash_id: str) -> str:
        """
        Create a new cache id for the lookup.

        :param identity_hash_id: the id of the object
        :return: the new lookup id
        """
        return self.__var_cache.new_var_id(identity_hash_id)

    def append_variable(self, var_id, variable):
        """
        Append a variable to the var lookup.

        This is called when a variable has been processed

        :param var_id: the internal id of the variable
        :param variable: the internal value of the variable
        """
        self.__var_lookup[var_id] = variable
