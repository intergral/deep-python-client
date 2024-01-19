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
Provide target for tests.

NOTE: the line numbers in this file are used in other tests when installing tracepoints. It is important therefore
that the line numbers of this file are changed carefully. As changes can result in lots of tests failures.
"""

import random


class BPSuperClass:
    """This is used to test the discovery of variables in super classes."""

    def __init__(self, name):
        self.__name = name
        self.__not_on_super = 11


class BPTargetTest(BPSuperClass):
    """This is a test class that is used by other tests as the target for tracepoints."""

    def __init__(self, name, i):
        super().__init__("i am a name" + name)
        self.__name = name
        self.__i = i

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    def call_something(self, val):
        return self.name + val

    def error_something(self, val):
        return len(val)

    def throw_something(self, val):
        raise Exception(val)

    def catch_something(self, val):
        try:
            raise Exception(val)
        except Exception as e:
            return str(e)

    def finally_something(self, val):
        try:
            raise Exception(val)
        except Exception as e:
            return str(e)
        finally:
            print("finally_something")

    def some_func_with_body(self, some_arg):
        name = self.__name
        new_name = name + some_arg
        i = random.randint(3, 9)
        return str(i) + new_name

    def some_func_with_body_long(self, some_arg):
        name = self.__name
        new_name = name + some_arg
        i = random.randint(3, 9)
        self.finally_something(some_arg)
        self.throw_something(some_arg)
        return str(i) + new_name
