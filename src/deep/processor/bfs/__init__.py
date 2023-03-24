import abc
from typing import Callable

from deep.api.tracepoint import VariableId


class Node:
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


class ParentNode(abc.ABC):
    @abc.abstractmethod
    def add_child(self, child: VariableId):
        raise NotImplementedError


class NodeValue:
    def __init__(self, name: str, value: any):
        self.name = name
        self.value = value


def breadth_first_search(node: 'Node', consumer: Callable[['Node'], bool]):
    queue = [node]

    while len(queue) != 0:
        pop = queue.pop()
        can_continue = consumer(pop)

        if can_continue:
            queue += pop.children
        else:
            return
