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

import random
from typing import List, Dict

from deep.api.attributes import BoundedAttributes
from deep.api.resource import Resource
from deep.utils import time_ns


class EventSnapshot:
    """
    This is the model for the snapshot that is uploaded to the services
    """

    def __init__(self, tracepoint, ts, resource, frames, var_lookup: Dict[str, 'Variable']):
        self._id = random.getrandbits(128)
        self._tracepoint = tracepoint
        self._var_lookup: Dict[str, 'Variable'] = var_lookup
        self._ts_nanos = ts
        self._frames = frames
        self._watches = []
        self._attributes = BoundedAttributes(immutable=False)
        self._duration_nanos = 0
        self._resource = Resource.get_empty().merge(resource)
        self._open = True

    def complete(self):
        if not self._open:
            return
        self._duration_nanos = time_ns() - self._ts_nanos
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
    def ts_nanos(self):
        return self._ts_nanos

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
    def duration_nanos(self):
        return self._duration_nanos

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
                 short_path,
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
        self._short_path = short_path
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
    def short_path(self):
        return self._short_path

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
    def children(self) -> List['VariableId']:
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
                 modifiers=None,
                 original_name=None
                 ):
        if modifiers is None:
            modifiers = []
        self._vid = vid
        self._name = name
        self._original_name = original_name
        self._modifiers = modifiers

    @property
    def vid(self):
        return self._vid

    @property
    def name(self):
        return self._name

    @property
    def original_name(self):
        return self._original_name

    @property
    def modifiers(self):
        return self._modifiers

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, o) -> bool:
        if not isinstance(o, VariableId):
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
