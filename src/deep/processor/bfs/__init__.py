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
from typing import Callable

from deep.api.tracepoint import VariableId


class Node:
    """This is a Node that is used within the Breadth First Search of variables."""
    def __init__(self, value=None, children=None, parent=None):
        if children is None:
            children = []
        self._value: 'NodeValue' = value
        self._children: list['Node'] = children
        self._parent: 'ParentNode' = parent
        self._depth = 0

    @property
    def parent(self) -> 'ParentNode':
        return self._parent

    @parent.setter
    def parent(self, parent: 'ParentNode'):
        self._parent = parent

    def add_children(self, children: list['Node']):
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
    def children(self) -> list['Node']:
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
    def __init__(self, name: str, value: any):
        self.name = name
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
