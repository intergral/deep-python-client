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

"""Types for the captured data."""

import random
from typing import Optional, Dict, List

from deep.api.attributes import BoundedAttributes
from deep.api.resource import Resource
from deep.utils import time_ns


class EventSnapshot:
    """This is the model for the snapshot that is uploaded to the services."""

    def __init__(self, tracepoint, ts, resource, frames, var_lookup: Dict[str, 'Variable']):
        """
        Create a new snapshot object.

        :param tracepoint: the tracepoint object
        :param ts: the time in nanoseconds
        :param resource: the client resource
        :param frames: the captured frames
        :param var_lookup: the captured variables.
        """
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
        self._log = None

    def complete(self):
        """Close and complete the snapshot."""
        if not self._open:
            return
        self._duration_nanos = time_ns() - self._ts_nanos
        self._open = False

    def is_open(self):
        """Is this snapshot still open."""
        return self._open

    def add_watch_result(self, watch_result: 'WatchResult'):
        """
        Append a watch result to the snapshot.

        :param watch_result: the result to append.
        :return:
        """
        if self.is_open():
            self.watches.append(watch_result)

    def merge_var_lookup(self, lookup: Dict[str, 'Variable']):
        """
        Merge additional variables into the var lookup.

        :param lookup:  the values to merge
        """
        if self.is_open():
            self._var_lookup.update(lookup)

    @property
    def id(self):
        """The id of this snapshot."""
        return self._id

    @property
    def tracepoint(self):
        """The tracepoint that triggered this snapshot."""
        return self._tracepoint

    @property
    def var_lookup(self):
        """The captured var lookup."""
        return self._var_lookup

    @property
    def ts_nanos(self):
        """The time in nanoseconds, this snapshot was triggered."""
        return self._ts_nanos

    @property
    def frames(self):
        """The captured frames."""
        return self._frames

    @property
    def watches(self):
        """The watch results."""
        return self._watches

    @property
    def attributes(self) -> BoundedAttributes:
        """The snapshot attributes."""
        return self._attributes

    @property
    def duration_nanos(self):
        """The duration in nanoseconds."""
        return self._duration_nanos

    @property
    def resource(self):
        """The client resource information."""
        return self._resource

    @property
    def log_msg(self):
        """Get the processed log message."""
        return self._log

    @log_msg.setter
    def log_msg(self, msg):
        """Set the processed log message."""
        self._log = msg

    def __str__(self) -> str:
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this as a string."""
        return self.__str__()


class StackFrame:
    """This represents a frame of code that is being executed."""

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
        """
        Create a new StackFrame object.

        :param file_name: The full file path
        :param short_path: The short file path
        :param method_name: The method name
        :param line_number: The line number
        :param variables: Variables captured on this frame
        :param class_name: The class name
        :param is_async: Is the frame an async frame
        :param column_number: The column number
        :param transpiled_file_name: The transpiled file name
        :param transpiled_line_number: The transpiled line number
        :param transpiled_column_number: The transpiled column number
        :param app_frame: Is this frame in the user app
        """
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
        """The full file path."""
        return self._file_name

    @property
    def short_path(self):
        """The short file path."""
        return self._short_path

    @property
    def method_name(self):
        """The method name."""
        return self._method_name

    @property
    def line_number(self):
        """The line number."""
        return self._line_number

    @property
    def class_name(self):
        """The class name."""
        return self._class_name

    @property
    def is_async(self):
        """Is the frame an async frame."""
        return self._async

    @property
    def column_number(self):
        """The column number."""
        return self._column_number

    @property
    def transpiled_file_name(self):
        """The transpiled file name."""
        return self._transpiled_file_name

    @property
    def transpiled_line_number(self):
        """The transpiled line number."""
        return self._transpiled_line_number

    @property
    def transpiled_column_number(self):
        """The transpiled column number."""
        return self._transpiled_column_number

    @property
    def variables(self):
        """Variables captured on this frame."""
        return self._variables

    @property
    def app_frame(self):
        """Is this frame in the user app."""
        return self._app_frame

    def __str__(self) -> str:
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this as a string."""
        return self.__str__()


class Variable:
    """This represents a captured variable value."""

    def __init__(self,
                 var_type,
                 value,
                 var_hash,
                 children,
                 truncated,
                 ):
        """
        Create a new Variable object.

        :param var_type: the type of the variable.
        :param value: the value as a string
        :param var_hash: the identity hash of the value
        :param children: list of child VariableIds
        :param truncated: is the value string truncated.
        """
        self._type = var_type
        self._value = value
        self._hash = var_hash
        self._children = children
        self._truncated = truncated

    @property
    def type(self):
        """The type of this value."""
        return self._type

    @property
    def value(self):
        """The string value of variable."""
        return self._value

    @property
    def hash(self):
        """The identity hash of this value."""
        return self._hash

    @property
    def children(self) -> List['VariableId']:
        """The children of this value."""
        return self._children

    @property
    def truncated(self):
        """Is the string value truncated."""
        return self._truncated

    def __str__(self) -> str:
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this as a string."""
        return self.__str__()


class VariableId:
    """
    This represents a variable id, that is used for de duplication.

    A VariableID is a pointer to a reference within the var lookup of the snapshot. Each VariableID can have
    different names and modifiers, but point to the same value.

    e.g.
     val = "Ben"
     name = val

    Both 'val' and 'name' have the value 'Ben' to prevent duplication of this in the var lookup, we use the
    VariableId to point to the value using the vid property.
    """

    def __init__(self,
                 vid,
                 name,
                 modifiers=None,
                 original_name=None
                 ):
        """
        Create a new variable object.

        :param vid: the variable id
        :param name: the variable name
        :param modifiers: the variable modifiers
        :param original_name: the original name
        """
        if modifiers is None:
            modifiers = []
        self._vid = vid
        self._name = name
        self._original_name = original_name
        self._modifiers = modifiers

    @property
    def vid(self):
        """Get variable id."""
        return self._vid

    @property
    def name(self):
        """Get variable name."""
        return self._name

    @property
    def original_name(self):
        """Get variable original name."""
        return self._original_name

    @property
    def modifiers(self):
        """Get variable modifiers."""
        return self._modifiers

    def __str__(self) -> str:
        """Represent this as a string."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """Represent this as a string."""
        return self.__str__()

    def __eq__(self, o) -> bool:
        """Check if the variable id matches."""
        if not isinstance(o, VariableId):
            return False

        if id(o) == id(self):
            return True

        return o._vid == self._vid and o._name == self._name and o._modifiers == self._modifiers


class WatchResult:
    """This is the result of a watch expression."""

    def __init__(self,
                 expression: str,
                 result: Optional['VariableId'],
                 error: Optional[str] = None
                 ):
        """
        Create new watch result.

        :param expression: the expression used
        :param result: the result of the expression
        :param error: the error captured during execution
        """
        self._expression = expression
        self._result = result
        self._error = error

    @property
    def expression(self) -> str:
        """The watch expression."""
        return self._expression

    @property
    def result(self) -> Optional['VariableId']:
        """The good result."""
        return self._result

    @property
    def error(self) -> Optional[str]:
        """The error."""
        return self._error
