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
    def check_id(self, identity_hash_id: str) -> str:
        """
        Check if the identity_hash_id is known to us, and return the lookup id
        :param identity_hash_id: the id of the object
        :return: the lookup id used
        """
        pass

    @abc.abstractmethod
    def new_var_id(self, identity_hash_id: str) -> str:
        """
        Create a new cache id for the lookup
        :param identity_hash_id: the id of the object
        :return: the new lookup id
        """
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


def var_modifiers(var_name: str) -> list[str]:
    """
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
    Convert the variable to a string
    :param variable_type: the variable type
    :param var_value: the variable value
    :return: a string of the value
    """
    if variable_type.__name__ in ITER_LIKE_TYPES:
        # if interator like then make a custom string - we do not want to mess with iterators
        return 'Object of type: %s' % variable_type
    elif variable_type is dict \
            or variable_type.__name__ in LIST_LIKE_TYPES:
        # if we are a collection then we do not want to use built in string as this can be very
        # large, and quite pointless, in stead we just get the size of the collection
        return 'Size: %s' % len(var_value)
    else:
        # everything else just gets a string value
        return str(var_value)


def process_variable(frame_collector: Collector, var_name: str, var_value: any) -> VariableResponse:
    """
    Process the variable into a serializable type.
    :param frame_collector: the collector being used
    :param var_name: the variable name
    :param var_value: the variable value
    :return: a response to determine if we continue
    """

    # get the variable hash id
    identity_hash_id = str(id(var_value))
    # guess the modifiers
    modifiers = var_modifiers(var_name)
    # check the collector cache for this id
    cache_id = frame_collector.check_id(identity_hash_id)
    # if we have a cache_id, then this variable is already been processed, so we just return
    # a variable id and do not process children. This prevents us from processing the same value over and over. We
    # also do not count this towards the max_vars, so we can increase the data we send.

    if cache_id is not None:
        return VariableResponse(VariableId(cache_id, var_name, modifiers), process_children=False)

    # if we do not have a cache_id - then create one
    var_id = frame_collector.new_var_id(identity_hash_id)

    # crete the variable id to use
    variable_id = VariableId(var_id, var_name, modifiers)
    # extract variable type
    variable_type = type(var_value)
    # create a string value of the variable
    variable_value_str, truncated = truncate_string(variable_to_string(variable_type, var_value),
                                                    frame_collector.frame_config.max_string_length)

    # create a variable for the lookup
    variable = Variable(str(variable_type.__name__), variable_value_str, identity_hash_id, [], truncated)
    # add to lookup
    frame_collector.append_variable(var_id, variable)
    # return result - and expand children
    return VariableResponse(variable_id, process_children=True)


def truncate_string(string, max_length):
    """
    Truncate the incoming string to the specified length
    :param string: the string to truncate
    :param max_length: the length to truncated to
    :return: a tuple of the new string, and if it was truncated
    """
    return string[:max_length], len(string) > max_length


def process_child_nodes(
        frame_collector: Collector,
        variable_id: str,
        var_value: any,
        frame_depth: int
) -> list[Node]:
    """
    Processing the children how we get the list of new variables to process. The method changes depending on
    the type we are processing.

    :param frame_collector: the collector we are using
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
    if frame_depth + 1 >= frame_collector.frame_config.max_var_depth:
        return []

    class VariableParent(ParentNode):

        def add_child(self, child: VariableId):
            # look for the child in the lookup and add this id to it
            frame_collector.add_child_to_lookup(variable_id, child)

    # scan the child based on type
    return find_children_for_parent(frame_collector, VariableParent(), var_value, variable_type)


def find_children_for_parent(frame_collector: Collector, parent_node: ParentNode, value: any,
                             variable_type: type):
    """
    Scan the parent for children based on the type
    :param frame_collector: the collector we are using
    :param parent_node: the parent node
    :param value: the variable value we are processing
    :param variable_type: the type of the variable
    :return: list of child nodes
    """
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
