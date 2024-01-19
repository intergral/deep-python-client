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

"""Provide type to store data based on the calling thread."""

import threading
from typing import TypeVar, Generic, Callable


T = TypeVar('T')


class ThreadLocal(Generic[T]):
    """This type offers the ability to store a value based on the thread that accessed the value."""

    __store = {}

    def __init__(self, default_provider: Callable[[], T] = lambda: None):
        """
        Create a new ThreadLocal value.

        :param default_provider: a provider that will produce a default value
        """
        self.__default_provider = default_provider

    def get(self) -> T:
        """
        Get the value stored for the calling thread.

        :return: the stored value, or the value from the default_provider
        """
        current_thread = threading.current_thread()
        get = self.__store.get(current_thread.ident, None)
        if get is None:
            get = self.__default_provider()
            self.__store[current_thread.ident] = get
        return get

    def set(self, val: T):
        """
        Set the value to get stored.

        :param val: the value to store
        """
        current_thread = threading.current_thread()
        self.__store[current_thread.ident] = val

    def clear(self):
        """Remove the value for this thread."""
        current_thread = threading.current_thread()
        if current_thread.ident in self.__store:
            del self.__store[current_thread.ident]

    @property
    def is_set(self):
        """
        Check if the value is set for this thread.

        :return: True if there is a value for this thread
        """
        current_thread = threading.current_thread()
        return current_thread.ident in self.__store

    @property
    def value(self):
        """
        Get the value stored for the calling thread.

        :return: the stored value, or the value from the default_provider
        """
        return self.get()

    @value.setter
    def value(self, value):
        """
        Set the value to get stored.

        :param value: the value to store
        """
        self.set(value)
