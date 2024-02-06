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

"""Handling for action context."""

import abc
from typing import Tuple, TYPE_CHECKING, Dict

import deep.logging
from deep.logging import logging
from deep.api.tracepoint import WatchResult, Variable
from deep.processor.variable_set_processor import VariableSetProcessor
from deep.utils import str2bool

if TYPE_CHECKING:
    from deep.processor.context.trigger_context import TriggerContext
    from deep.api.tracepoint.trigger import LocationAction


class ActionContext(abc.ABC):
    """A context for the processing of an action."""

    def __init__(self, parent: 'TriggerContext', action: 'LocationAction'):
        """
        Create a new action context.

        :param parent: the parent trigger
        :param action: the action config
        """
        self.trigger_context: 'TriggerContext' = parent
        self.location_action: 'LocationAction' = action
        self._triggered = False

    def __enter__(self):
        """Enter and open the context."""
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Exit and close the context."""
        if self.has_triggered():
            self.location_action.record_triggered(self.trigger_context.ts)

    def eval_watch(self, watch: str) -> Tuple[WatchResult, Dict[str, Variable], str]:
        """
        Evaluate an expression in the current frame.

        :param watch: The watch expression to evaluate.
        :return: Tuple with WatchResult, collected variables, and the log string for the expression
        """
        var_processor = VariableSetProcessor({}, self.trigger_context.var_cache)

        try:
            result = self.trigger_context.evaluate_expression(watch)
            variable_id, log_str = var_processor.process_variable(watch, result)

            return WatchResult(watch, variable_id), var_processor.var_lookup, log_str
        except BaseException as e:
            logging.exception("Error evaluating watch %s", watch)
            return WatchResult(watch, None, str(e)), {}, str(e)

    def process(self):
        """Process the action."""
        try:
            return self._process_action()
        finally:
            self._triggered = True

    @abc.abstractmethod
    def _process_action(self):
        pass

    def has_triggered(self):
        """
        Check if we have triggerd during this context.

        :return: True, if the trigger has been fired.
        """
        return self._triggered

    def can_trigger(self) -> bool:
        """
        Check if the action can trigger.

        Combine checks for rate limits, windows and condition.
        :return: True, if the trigger can be triggered.
        """
        if not self.location_action.can_trigger(self.trigger_context.ts):
            return False
        if self.location_action.condition is None or len(self.location_action.condition.strip()) == 0:
            return True
        result = self.trigger_context.evaluate_expression(self.location_action.condition)
        return str2bool(str(result))


class NoActionContext(ActionContext):
    """Default context if no action can be determined."""

    def _process_action(self):
        deep.logging.error("Unsupported action type: %s", self.location_action)
