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

import random

from deep.api.attributes import BoundedAttributes
from deep.api.resource import Resource
from deep.utils import time_ms, time_ns


class EventSnapshot:
    """
    This is the model for the snapshot that is uploaded to the services
    """
    def __init__(self, tracepoint, frames, var_lookup: dict[str, 'Variable']):
        self._id = random.getrandbits(128)
        self._tracepoint = tracepoint
        self._var_lookup: dict[str, 'Variable'] = var_lookup
        self._ts = time_ms()
        self._frames = frames
        self._watches = []
        self._attributes = BoundedAttributes()
        self._nanos_duration = time_ns()
        self._resource = Resource.create()
        self._open = True

    def complete(self):
        if not self._open:
            return
        self._nanos_duration = time_ns() - self._nanos_duration
        self._open = False

    def is_open(self):
        return self._open

    def add_watch_result(self, watch_result, watch_lookup):
        if self.is_open():
            self.watches.append(watch_result)
            self._var_lookup.update(watch_lookup)

    @property
    def id(self):
        return self._id

    @property
    def tracepoint(self):
        return self._tracepoint

    @property
    def var_lookup(self):
        return self._var_lookup

    @property
    def ts(self):
        return self._ts

    @property
    def frames(self):
        return self._frames

    @property
    def watches(self):
        return self._watches

    @property
    def attributes(self) -> BoundedAttributes:
        return self._attributes

    @property
    def nanos_duration(self):
        return self._nanos_duration

    @property
    def resource(self):
        return self._resource

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class StackFrame:
    """
    This represents a frame of code that is being executed
    """
    def __init__(self,
                 file_name,
                 method_name,
                 line_number,
                 variables,
                 class_name,
                 is_async=False,
                 column_number=0,
                 transpiled_file_name=None,
                 transpiled_line_number=0,
                 transpiled_column_number=0,
                 app_frame=False
                 ):
        self._file_name = file_name
        self._method_name = method_name
        self._line_number = line_number
        self._class_name = class_name
        self._async = is_async
        self._column_number = column_number
        self._transpiled_file_name = transpiled_file_name
        self._transpiled_line_number = transpiled_line_number
        self._transpiled_column_number = transpiled_column_number
        self._variables = variables
        self._app_frame = app_frame

    @property
    def file_name(self):
        return self._file_name

    @property
    def method_name(self):
        return self._method_name

    @property
    def line_number(self):
        return self._line_number

    @property
    def class_name(self):
        return self._class_name

    @property
    def is_async(self):
        return self._async

    @property
    def column_number(self):
        return self._column_number

    @property
    def transpiled_file_name(self):
        return self._transpiled_file_name

    @property
    def transpiled_line_number(self):
        return self._transpiled_line_number

    @property
    def transpiled_column_number(self):
        return self._transpiled_column_number

    @property
    def variables(self):
        return self._variables

    @property
    def app_frame(self):
        return self._app_frame

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Variable:
    """This represents a captured variable value"""
    def __init__(self,
                 var_type,
                 value,
                 var_hash,
                 children,
                 truncated,
                 ):
        self._type = var_type
        self._value = value
        self._hash = var_hash
        self._children = children
        self._truncated = truncated

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    @property
    def hash(self):
        return self._hash

    @property
    def children(self) -> list['VariableId']:
        return self._children

    @property
    def truncated(self):
        return self._truncated

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class VariableId:
    """
    This represents an variable id, that is used for de duplication
    """
    def __init__(self,
                 vid,
                 name,
                 modifiers=None
                 ):
        if modifiers is None:
            modifiers = []
        self._vid = vid
        self._name = name
        self._modifiers = modifiers

    @property
    def vid(self):
        return self._vid

    @property
    def name(self):
        return self._name

    @property
    def modifiers(self):
        return self._modifiers

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, o) -> bool:
        if type(o) != VariableId:
            return False

        if id(o) == id(self):
            return True

        return o._vid == self._vid and o._name == self._name and o._modifiers == self._modifiers


class WatchResult:
    """
    This is the result of a watch expression
    """

    def __init__(self,
                 expression,
                 result,
                 error=None
                 ):
        self._expression = expression
        self._result = result
        self._error = error

    @property
    def expression(self):
        return self._expression

    @property
    def result(self):
        return self._result

    @property
    def error(self):
        return self._error
