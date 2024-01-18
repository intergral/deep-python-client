#       Copyright (C) 2024  Intergral GmbH
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

"""Utils used for making testing easier."""

# noinspection PyProtectedMember
from mockito.matchers import Matcher

from deep.api.resource import Resource
from deep.api.tracepoint import TracePointConfig, EventSnapshot, StackFrame, VariableId, Variable
from deep.utils import time_ns


def mock_tracepoint(**kwargs) -> TracePointConfig:
    """
    Create a tracepoint while defaulting arguments if not set.

    :param kwargs: the arguments to set on the tracepoint
    :return: the new tracepoint
    """
    if 'tp_id' not in kwargs:
        kwargs['tp_id'] = "tp_id"
    if 'path' not in kwargs:
        kwargs['path'] = "some_test.py"
    if 'line_no' not in kwargs:
        kwargs['line_no'] = 123
    if 'args' not in kwargs:
        kwargs['args'] = {}
    if 'watches' not in kwargs:
        kwargs['watches'] = []
    if 'metrics' not in kwargs:
        kwargs['metrics'] = []

    return TracePointConfig(**kwargs)


def mock_snapshot(**kwargs) -> EventSnapshot:
    """
    Create a snapshot while defaulting arguments if not set.

    :param kwargs: the arguments to set on the snapshot
    :return: the new snapshot
    """
    if 'tracepoint' not in kwargs:
        kwargs['tracepoint'] = mock_tracepoint()
    if 'ts' not in kwargs:
        kwargs['ts'] = time_ns()
    if 'resource' not in kwargs:
        kwargs['resource'] = Resource.get_empty()
    if 'frames' not in kwargs:
        kwargs['frames'] = []
    if 'var_lookup' not in kwargs:
        kwargs['var_lookup'] = {}

    return EventSnapshot(**kwargs)


def mock_frame(**kwargs) -> StackFrame:
    """
    Create a frame while defaulting arguments if not set.

    :param kwargs: the arguments to set on the frame
    :return: the new frame
    """
    if 'file_name' not in kwargs:
        kwargs['file_name'] = 'file_name'
    if 'short_path' not in kwargs:
        kwargs['short_path'] = 'short_path'
    if 'method_name' not in kwargs:
        kwargs['method_name'] = 'method_name'
    if 'line_number' not in kwargs:
        kwargs['line_number'] = 123
    if 'variables' not in kwargs:
        kwargs['variables'] = {}
    if 'class_name' not in kwargs:
        kwargs['class_name'] = 'class_name'

    return StackFrame(**kwargs)


def mock_variable_id(**kwargs) -> VariableId:
    """
    Create a variable id while defaulting arguments if not set.

    :param kwargs: the arguments to set on the variable id
    :return: the new variable id
    """
    if 'vid' not in kwargs:
        kwargs['vid'] = 'vid'
    if 'name' not in kwargs:
        kwargs['name'] = 'name'

    return VariableId(**kwargs)


def mock_variable(**kwargs) -> Variable:
    """
    Create a variable while defaulting arguments if not set.

    :param kwargs: the arguments to set on the variable
    :return: the new variable
    """
    if 'var_type' not in kwargs:
        kwargs['var_type'] = 'str'
    if 'value' not in kwargs:
        kwargs['value'] = 'name'
    if 'var_hash' not in kwargs:
        kwargs['var_hash'] = '17117'
    if 'children' not in kwargs:
        kwargs['children'] = []
    if 'truncated' not in kwargs:
        kwargs['truncated'] = False

    return Variable(**kwargs)


class Captor(Matcher):
    """Use with mockito to capture values passed ot mocks."""

    def __init__(self, to_dict=False):
        """Create new Captor."""
        self.values = []
        self.to_dict = to_dict

    def matches(self, arg):
        """Validate the value matches the expected value."""
        if self.to_dict:
            self.values.append(arg.as_dict())
        else:
            self.values.append(arg)
        return True

    def get_value(self):
        """Get the captured value."""
        if len(self.values) > 0:
            return self.values[len(self.values) - 1]
        return None

    def get_values(self):
        """Get all captured values."""
        return self.values
