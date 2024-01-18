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
Breadth first search functions.

To improve the performance and usefulness of the variable data gathered we use a Breadth First Search (BFS)
approach. This means scanning all local values before proceeding to the next depth on each.
"""

import abc
from typing import Callable, List

from deep.api.tracepoint import VariableId


class Node:
    """This is a Node that is used within the Breadth First Search of variables."""

    def __init__(self, value: 'NodeValue' = None, children: List['Node'] = None, parent: 'ParentNode' = None):
        """
        Create a new node to process.

        :param (NodValue) value: the value to process
        :param (list) children: the child nodes for this value
        :param (ParentNode) parent: the parent node for this node
        """
        if children is None:
            children = []
        self._value: 'NodeValue' = value
        self._children: List['Node'] = children
        self._parent: 'ParentNode' = parent
        self._depth = 0

    @property
    def parent(self) -> 'ParentNode':
        """Get the parent node."""
        return self._parent

    @parent.setter
    def parent(self, parent: 'ParentNode'):
        """Set the parent node."""
        self._parent = parent

    def add_children(self, children: List['Node']):
        """
        Add children to this node.

        :param (list) children: the children to add
        """
        for child in children:
            child._depth = self._depth + 1
            self._children.append(child)

    @property
    def value(self) -> 'NodeValue':
        """The node value."""
        return self._value

    @property
    def depth(self):
        """The node value."""
        return self._depth

    @property
    def children(self) -> List['Node']:
        """The node children."""
        return self._children

    def __str__(self) -> str:
        """Convert to string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Convert to string."""
        return self.__str__()


class ParentNode(abc.ABC):
    """This represents the parent node - simple used to attach children to the parent if they are processed."""

    @abc.abstractmethod
    def add_child(self, child: VariableId):
        """
        Add a child to this parent.

        :param child: the child to add.
        """
        raise NotImplementedError


class NodeValue:
    """The variable value the node represents."""

    def __init__(self, name: str, value: any, original_name=None):
        """
        Create a new node value.

        It is possible to rename variables by providing an original name. This is used when dealing with
        'private' variables in classes.

        e.g. A variable called _NodeValue__name is used by python to represent the private variable __name. This
         is not known by devs, so we rename the variable to __name, and keep the original name as _NodeValue__name,
         so we can show this if required.

        :param name: the name of the variable at this scope.
        :param value: the value of the variable
        :param original_name: the original name
        """
        self.name = name
        if original_name is not None and name != original_name:
            self.original_name = original_name
        else:
            self.original_name = None
        self.value = value

    def __str__(self) -> str:
        """Parse the value into a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Parse the value into a string."""
        return self.__str__()


def breadth_first_search(node: 'Node', consumer: Callable[['Node'], bool]):
    """
    Search for variables using BFS.

    Starting from the provided node, and using the consumer. Search for variables using BFS.

    We call consume, which will add all the child nodes to thr passed node. The return will then tell us to process
    these or not. If we process them then we append the children to the queue.

    By using this queue approach we will process all the top level variables, then all of their children, and so
    on until we are complete.

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
