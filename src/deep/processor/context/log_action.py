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

"""Handling for log actions."""

from typing import TYPE_CHECKING, List, Dict, Optional

from .action_context import ActionContext
from .action_results import ActionResult, ActionCallback
from ...api.tracepoint.constants import LOG_MSG
from ...api.tracepoint.trigger import LocationAction

from typing import Tuple

if TYPE_CHECKING:
    from ...api.tracepoint import WatchResult, Variable
    from .trigger_context import TriggerContext


class LogActionContext(ActionContext):
    """The context for processing a log action."""

    def _process_action(self):
        log_msg = self.location_action.config.get(LOG_MSG)
        log, watches, vars_ = self.process_log(log_msg)
        self.trigger_context.attach_result(LogActionResult(self.location_action, log))

    def process_log(self, log_msg) -> Tuple[str, List['WatchResult'], Dict[str, 'Variable']]:
        """
        Process the log message.

        :param log_msg: the configure log message

        :returns:
            (str) process_log: the result of the processed log
            (list) watch: the watch results from the expressions
            (dic) vars: the collected variables
        """
        ctx_self = self
        watch_results = []
        _var_lookup = {}

        class FormatDict(dict):
            """This type is used in the log process to ensure that missing values are formatted don't error."""

            def __missing__(self, key):
                return "{%s}" % key

        import string

        class FormatExtractor(string.Formatter):
            """
            Allows logs to be formatted correctly.

            This type allows us to use watches within log strings and collect the watch
            as well as interpolate the values.
            """

            def get_field(self, field_name, args, kwargs):
                # evaluate watch
                watch, var_lookup, log_str = ctx_self.eval_watch(field_name)
                # collect data
                watch_results.append(watch)
                _var_lookup.update(var_lookup)

                return log_str, field_name

        log_msg = "[deep] %s" % FormatExtractor().vformat(log_msg, (), FormatDict(self.trigger_context.locals))
        return log_msg, watch_results, _var_lookup


class LogActionResult(ActionResult):
    """The result of a successful log action."""

    def __init__(self, action: 'LocationAction', log: str):
        """
        Create a new result of a log action.

        :param action: the source action
        :param log: the log result.
        """
        self.action = action
        self.log = log

    def process(self, ctx: 'TriggerContext') -> Optional[ActionCallback]:
        """
        Process this result.

        :param ctx: the triggering context

        :return: an action callback if we need to do something at the 'end', or None
        """
        tracepoint_logger = ctx.config.tracepoint_logger
        if tracepoint_logger:
            tracepoint_logger.log_tracepoint(self.log, ctx.id, self.action.id)
        return None
