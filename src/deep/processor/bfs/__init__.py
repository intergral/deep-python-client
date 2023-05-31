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

import abc
from typing import Callable, List

from deep.api.tracepoint import VariableId


class Node:
    """This is a Node that is used within the Breadth First Search of variables."""

    def __init__(self, value=None, children: List['Node'] = None, parent=None):
        if children is None:
            children = []
        self._value: 'NodeValue' = value
        self._children: List['Node'] = children
        self._parent: 'ParentNode' = parent
        self._depth = 0

    @property
    def parent(self) -> 'ParentNode':
        return self._parent

    @parent.setter
    def parent(self, parent: 'ParentNode'):
        self._parent = parent

    def add_children(self, children: List['Node']):
        for child in children:
            child._depth = self._depth + 1
            self._children.append(child)

    @property
    def value(self) -> 'NodeValue':
        return self._value

    @property
    def depth(self):
        return self._depth

    @property
    def children(self) -> List['Node']:
        return self._children

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class ParentNode(abc.ABC):
    """This represents the parent node - simple used to attach children to the parent if they are processed"""

    @abc.abstractmethod
    def add_child(self, child: VariableId):
        raise NotImplementedError


class NodeValue:
    """The variable value the node represents"""

    def __init__(self, name: str, value: any, original_name=None):
        self.name = name
        if original_name is not None and name != original_name:
            self.original_name = original_name
        else:
            self.original_name = None
        self.value = value

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


def breadth_first_search(node: 'Node', consumer: Callable[['Node'], bool]):
    """
    To improve the performance and usefulness of the variable data gathered we use a Breadth First Search (BFS)
    approach. This means scanning all local values before proceeding to the next depth on each.

    :param node: the initial node to start the search
    :param consumer: the consumer to call on each node
    """
    queue = [node]

    while len(queue) != 0:
        pop = queue.pop()
        can_continue = consumer(pop)

        if can_continue:
            queue += pop.children
        else:
            return
