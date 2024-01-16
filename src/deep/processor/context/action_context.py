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
import abc
from typing import Tuple, TYPE_CHECKING

from deep import logging
from deep.api.tracepoint import WatchResult, Variable
from deep.api.tracepoint.trigger import LocationAction
from deep.processor.variable_set_processor import VariableSetProcessor
from deep.utils import str2bool

if TYPE_CHECKING:
    from deep.processor.context.trigger_context import TriggerContext


class ActionContext(abc.ABC):

    def __init__(self, parent: 'TriggerContext', action: 'LocationAction'):
        self._parent: 'TriggerContext' = parent
        self._action: 'LocationAction' = action
        self._triggered = False

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        if self.has_triggered():
            self._action.record_triggered(self._parent.ts)

    def eval_watch(self, watch: str) -> Tuple[WatchResult, dict[str, Variable], str]:
        """
        Evaluate an expression in the current frame.
        :param watch: The watch expression to evaluate.
        :return: Tuple with WatchResult, collected variables, and the log string for the expression
        """
        var_processor = VariableSetProcessor({}, self._parent.var_cache)

        try:
            result = self._parent.evaluate_expression(watch)
            variable_id, log_str = var_processor.process_variable(watch, result)

            return WatchResult(watch, variable_id), var_processor.var_lookup, log_str
        except BaseException as e:
            logging.exception("Error evaluating watch %s", watch)
            return WatchResult(watch, None, str(e)), {}, str(e)

    def process(self):
        try:
            return self._process_action()
        finally:
            self._triggered = True

    @abc.abstractmethod
    def _process_action(self):
        pass

    def has_triggered(self):
        return self._triggered

    def can_trigger(self) -> bool:
        if not self._action.can_trigger(self._parent.ts):
            return False
        if self._action.condition is None:
            return True
        result = self._parent.evaluate_expression(self._action.condition)
        return str2bool(str(result))


class MetricActionContext(ActionContext):

    def _process_action(self):
        print("metric action")
        pass


class SpanActionContext(ActionContext):

    def _process_action(self):
        print("span action")
        pass


class NoActionContext(ActionContext):

    def _process_action(self):
        print("Unsupported action type: %s" % self._action)