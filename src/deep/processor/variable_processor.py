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

"""
A set of functions to collect and process variable data.

There are many things to consider when collecting that data from a variable. Here we try to manage the collection
as best we can without affecting the original data source. As a result we have different ways to collect the data
and many options to consider when collecting.
"""

import abc
from typing import List

from deep import logging
from deep.api.tracepoint import VariableId, Variable
from .bfs import Node, ParentNode, NodeValue

NO_CHILD_TYPES = [
    'str',
    'int',
    'float',
    'bool',
    'type',
    'module',
    'unicode',
    'long',
]
"""A list of types that do not have child nodes, or only have child nodes we do not want to process."""

LIST_LIKE_TYPES = [
    'frozenset',
    'set',
    'list',
    'tuple',
]
"""A list of types that we should handle like lists."""

ITER_LIKE_TYPES = [
    'list_iterator',
    'listiterator',
    'list_reverseiterator',
    'listreverseiterator',
]
"""A list of types that we should handle like iterators."""

# We cannot process child nodes of iterators so add the iterator types to the no child types.
NO_CHILD_TYPES += ITER_LIKE_TYPES


class Collector(abc.ABC):
    """A type that is used to manage variable collection."""

    @property
    @abc.abstractmethod
    def max_string_length(self) -> int:
        """
        Get the max length of a string.

        :return int: the configured value
        """
        pass

    @property
    @abc.abstractmethod
    def max_collection_size(self) -> int:
        """
        Get the max size of a collection.

        :return int: the configured value
        """
        pass

    @property
    @abc.abstractmethod
    def max_var_depth(self) -> int:
        """
        Get the max depth to process.

        :return int: the configured value
        """
        pass

    @abc.abstractmethod
    def check_id(self, identity_hash_id: str) -> str:
        """
        Check if the identity_hash_id is known to us, and return the lookup id.

        :param identity_hash_id: the id of the object
        :return: the lookup id used
        """
        pass

    @abc.abstractmethod
    def new_var_id(self, identity_hash_id: str) -> str:
        """
        Create a new cache id for the lookup.

        :param identity_hash_id: the id of the object
        :return: the new lookup id
        """
        pass

    @abc.abstractmethod
    def append_variable(self, var_id: str, variable: Variable):
        """
        Append a variable to the var lookup.

        This is called when a variable has been processed

        :param var_id: the internal id of the variable
        :param variable: the internal value of the variable
        """
        pass

    @abc.abstractmethod
    def append_child(self, variable_id: str, child: VariableId):
        """
        Append a chile to existing variable.

        This is called when a child variable has been processed and the result should be attached to a
        variable that has already been processed.

        :param str variable_id: the internal variable id of the parent variable
        :param VariableId child: the internal variable id value to attach to the parent
        """
        pass


class VariableResponse:
    """The response from processing a variable."""

    def __init__(self, variable_id, process_children=True):
        """Create a new response object."""
        self.__variable_id = variable_id
        self.__process_children = process_children

    @property
    def variable_id(self):
        """The variable id data for the processed variable."""
        return self.__variable_id

    @property
    def process_children(self):
        """Continue with the child nodes."""
        return self.__process_children


def var_modifiers(var_name: str) -> List[str]:
    """
    Process access modifiers.

    Python does not have true access modifiers. The convention is to use leading underscores, one for
    protected, two for private.

    https://www.geeksforgeeks.org/access-modifiers-in-python-public-private-and-protected/

    :param var_name: the name to check
    :return: a list of the modifiers, or an empty list
    """
    if var_name.startswith("__"):
        return ['private']
    if var_name.startswith("_"):
        return ['protected']
    return []


def variable_to_string(variable_type, var_value):
    """
    Convert the variable to a string.

    :param variable_type: the variable type
    :param var_value: the variable value
    :return: a string of the value
    """
    if variable_type.__name__ in ITER_LIKE_TYPES:
        # if interator like then make a custom string - we do not want to mess with iterators
        return 'Iterator of type: %s' % variable_type
    elif variable_type is dict \
            or variable_type.__name__ in LIST_LIKE_TYPES:
        # if we are a collection then we do not want to use built in string as this can be very
        # large, and quite pointless, instead we just get the size of the collection
        return 'Size: %s' % len(var_value)
    else:
        try:
            # everything else just gets a string value
            return str(var_value)
        except Exception:
            # it is possible for str to fail if there is a custom __str__ function
            return f'{type(var_value)}@{id(var_value)}'


def process_variable(var_collector: Collector, node: NodeValue) -> VariableResponse:
    """
    Process the variable into a serializable type.

    :param var_collector: the collector being used
    :param node: the variable node to process
    :return: a response to determine if we continue
    """
    # get the variable hash id
    identity_hash_id = str(id(node.value))
    # guess the modifiers
    modifiers = var_modifiers(node.name)
    # check the collector cache for this id
    cache_id = var_collector.check_id(identity_hash_id)
    # if we have a cache_id, then this variable is already been processed, so we just return
    # a variable id and do not process children. This prevents us from processing the same value over and over. We
    # also do not count this towards the max_vars, so we can increase the data we send.

    if cache_id is not None:
        return VariableResponse(VariableId(cache_id, node.name, modifiers, node.original_name), process_children=False)

    # if we do not have a cache_id - then create one
    var_id = var_collector.new_var_id(identity_hash_id)

    # crete the variable id to use
    variable_id = VariableId(var_id, node.name, modifiers, node.original_name)
    # extract variable type
    variable_type = type(node.value)
    # create a string value of the variable
    variable_value_str, truncated = truncate_string(variable_to_string(variable_type, node.value),
                                                    var_collector.max_string_length)

    # create a variable for the lookup
    variable = Variable(str(variable_type.__name__), variable_value_str, identity_hash_id, [], truncated)
    # add to lookup
    var_collector.append_variable(var_id, variable)
    # return result - and expand children
    return VariableResponse(variable_id, process_children=True)


def truncate_string(string, max_length):
    """
    Truncate the incoming string to the specified length.

    :param string: the string to truncate
    :param max_length: the length to truncated to
    :return: a tuple of the new string, and if it was truncated
    """
    return string[:max_length], len(string) > max_length


def process_child_nodes(
        var_collector: Collector,
        variable_id: str,
        var_value: any,
        frame_depth: int
) -> List[Node]:
    """
    Collect the child nodes for this variable.

    Child node collection is performed via a variety of functions based on the type of the variable we are processing.

    :param var_collector: the collector we are using
    :param variable_id: the variable if to attach children to
    :param var_value: the value we are looking at for children
    :param frame_depth: the current depth we are at
    :return:
    """
    variable_type = type(var_value)
    # if the type is a type we do not want children from - return empty
    if variable_type.__name__ in NO_CHILD_TYPES:
        return []

    # if the depth is more than we are configured - return empty
    if frame_depth + 1 >= var_collector.max_var_depth:
        return []

    class VariableParent(ParentNode):

        def add_child(self, child: VariableId):
            # look for the child in the lookup and add this id to it
            var_collector.append_child(variable_id, child)

    # scan the child based on type
    return find_children_for_parent(var_collector, VariableParent(), var_value, variable_type)


def correct_names(name, val):
    """
    If a value is 'private' then python will rename the value to be prefixed with the class name.

    :param name: the name of the class
    :param val: the variable name we are modifying
    :return: the new name to use
    """
    prefix = "_" + name
    if val.startswith(prefix):
        return val[len(prefix):]
    return val


def find_children_for_parent(var_collector: Collector, parent_node: ParentNode, value: any,
                             variable_type: type):
    """
    Scan the parent for children based on the type.

    :param var_collector: the collector we are using
    :param parent_node: the parent node
    :param value: the variable value we are processing
    :param variable_type: the type of the variable
    :return: list of child nodes
    """
    if variable_type is dict:
        return process_dict_breadth_first(parent_node, variable_type.__name__, value)
    elif variable_type.__name__ in LIST_LIKE_TYPES:
        return process_list_breadth_first(var_collector, parent_node, value)
    elif isinstance(value, Exception):
        return process_list_breadth_first(var_collector, parent_node, value.args)
    elif hasattr(value, '__class__'):
        return process_dict_breadth_first(parent_node, variable_type.__name__, value.__dict__, correct_names)
    elif hasattr(value, '__dict__'):
        return process_dict_breadth_first(parent_node, variable_type.__name__, value.__dict__)
    else:
        logging.debug("Unknown type processed %s", variable_type)
        return []


def process_dict_breadth_first(parent_node, type_name, value, func=lambda x, y: y) -> List[Node]:
    """
    Process a dict value.

    Take a dict and collect all the child nodes for the dict.

    :param (ParentNode) parent_node: the node that represents the list, to be used as the parent for the returned nodes
    :param (str) type_name: the name of the type we are processing
    :param (any) value: the list value to process
    :param (Callable) func: an optional function to preprocess values

    :param func:
    :return (list): the collected child nodes
    """
    # we wrap the keys() in a call to list to prevent concurrent changes
    return [Node(value=NodeValue(func(type_name, key), value[key], key), parent=parent_node) for key in
            list(value.keys()) if
            key in value]


def process_list_breadth_first(var_collector: Collector, parent_node: ParentNode, value) -> List[Node]:
    """
    Process a list value.

    Take a list and collect all the child nodes for the list. Returned list is
    limited by the config 'max_collection_size'.

    :param (Collector) var_collector: the collector that is managing this collection
    :param (ParentNode) parent_node: the node that represents the list, to be used as the parent for the returned nodes
    :param (any) value: the list value to process
    :return (list): the collected child nodes
    """
    nodes = []
    total = 0
    for val_ in tuple(value):
        if total >= var_collector.max_collection_size:
            break
        nodes.append(Node(value=NodeValue(str(total), val_), parent=parent_node))
        total += 1
    return nodes
