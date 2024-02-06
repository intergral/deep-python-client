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

"""Handling for action callbacks."""
from types import FrameType
from typing import List

from deep.api.tracepoint.trigger import Location

from deep.processor.context.action_results import ActionCallback


class CallbackContext(Location, ActionCallback):
    """
    Callback Context deals with ensuring we close any pending actions created by TriggerHandler.

    If a span is created on a line or method, then we attach a callback that will trigger the span
    to close when the line/method completes.
    """

    def __init__(self, event: str, filename: str, line: int, name: str, callbacks: List['ActionCallback']):
        """Create new callback context."""
        super().__init__(Location.Position.END)
        self.__event = event
        self.__filename = filename
        self.__function_name = name
        self.__line = line
        self.__callbacks = callbacks

    def at_location(self, event: str, file: str, line: int, function_name: str, frame: FrameType) -> bool:
        """
        Check if we are at the location defined by this location.

        :param event: the trigger event
        :param file: the file path
        :param line: the line number
        :param function_name: the function name
        :param frame: the triggering frame object
        :return: True, if we are at this location we expect, else False.
        """
        # if either the file or function name are different, then we are not in the correct place.
        if file != self.__filename or function_name != self.__function_name:
            return False

        if self.__event == 'line':
            return self.__check_at_next_line(event, file, function_name)
        else:
            return self.__check_at_method_end(event)

    def process(self, event: str, frame: FrameType, arg: any):
        """
        Process all callbacks.

        :param event: the event
        :param frame: the frame data
        :param arg: the arg from settrace
        :return: True, to keep this callback until next match.
        """
        for callback in self.__callbacks:
            callback.process(event, frame, arg)

    @property
    def id(self) -> str:
        """The location id."""
        return "%s#%s" % (self.path, self.name)

    @property
    def path(self) -> str:
        """The source file path."""
        return self.__filename

    @property
    def line(self) -> int:
        """The source line number."""
        return self.__line

    @property
    def name(self) -> str:
        """The function name."""
        return self.__function_name

    def __check_at_next_line(self, event: str, file: str, function_name: str) -> bool:
        """
        Check if the new position is the next line after that which triggered this line event.

        When a 'line' event triggers a callback, then we are trying to track a line execution. This means we should
        trigger the callback when we are at the next logical line. This would be either the next 'line' event in the
        same file/function, or the 'exception' or 'return' event for the file/function that triggered the callback.

        :param event: the current event
        :param file: the current file
        :param function_name: the current function
        :return: True, if we are the next logical line of code.
        """
        # if we are at a new line event, then we want to check the file/line number
        if event == 'line':
            # if we are the same file and function then we are the next line
            if file == self.__filename and function_name == self.__function_name:
                return True
            # if we are line, but not the same file and function then we are not in the correct place
            return False

        # If we are not line, then we have to be the return or error from the method we started in
        return True

    def __check_at_method_end(self, event: str) -> bool:
        """
        Check if the new position is the end of the method we are wrapping.

        When a 'call' event triggers a callback, then we are trying to wrap a method execution. This means we should
        trigger the callback when the method ends. this is when the event 'exception' or 'return' is seen with the
        same file and function name.

        :param event: the current event
        :return: True, if we are the next logical line of code.

        """
        if event in ['exception', 'return']:
            return True
        return False
