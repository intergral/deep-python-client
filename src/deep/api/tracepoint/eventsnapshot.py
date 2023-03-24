import uuid

from deep.api.attributes import BoundedAttributes
from deep.api.resource import Resource
from deep.utils import time_ms, time_ns


class IllegalStateException(BaseException):
    pass


class EventSnapshot:
    def __init__(self, tracepoint):
        self._id = uuid.uuid4().hex
        self._tracepoint = tracepoint
        self._var_lookup = {}
        self._ts = time_ms()
        self._frames = []
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
    def attributes(self):
        return self._attributes

    @property
    def nanos_duration(self):
        return self._nanos_duration

    @property
    def resource(self):
        return self._resource

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return self._id


class StackFrame:
    def __init__(self, file_name,
                 method_name,
                 line_number,
                 variables,
                 class_name,
                 is_async=False,
                 column_number=0,
                 transpiled_file_name=None,
                 transpiled_line_number=0,
                 transpiled_column_number=0,
                 app_frame=False):
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


class Variable:
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
    def children(self):
        return self._children

    @property
    def truncated(self):
        return self._truncated


class VariableId:
    def __init__(self,
                 vid,
                 name,
                 modifiers
                 ):
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


class WatchResult:
    def __init__(self,
                 expression,
                 result
                 ):
        self._expression = expression
        self._result = result

    @property
    def expression(self):
        return self._expression

    @property
    def result(self):
        return self._result
