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
from typing import TYPE_CHECKING

from .action_context import ActionContext
from .action_results import ActionResult, ActionCallback
from ...api.tracepoint.constants import LOG_MSG
from ...logging.tracepoint_logger import TracepointLogger
from ...push import PushService

from typing import Tuple
if TYPE_CHECKING:
    from ...api.tracepoint import WatchResult, Variable, LocationAction

class LogActionContext(ActionContext):

    def _process_action(self):
        log_msg = self._action.config.get(LOG_MSG)
        log, watches, vars_ = self.process_log(log_msg)
        self._parent.attach_result(LogActionResult(self._action, log))

    def process_log(self, log_msg) -> Tuple[str, list['WatchResult'], dict[str, 'Variable']]:
        ctx_self = self
        watch_results = []
        _var_lookup = {}

        class FormatDict(dict):
            """This type is used in the log process to ensure that missing values are formatted don't error"""

            def __missing__(self, key):
                return "{%s}" % key

        import string

        class FormatExtractor(string.Formatter):
            """This type allows us to use watches within log strings and collect the watch
            as well as interpolate the values"""

            def get_field(self, field_name, args, kwargs):
                # evaluate watch
                watch, var_lookup, log_str = ctx_self.eval_watch(field_name)
                # collect data
                watch_results.append(watch)
                _var_lookup.update(var_lookup)

                return log_str, field_name

        log_msg = "[deep] %s" % FormatExtractor().vformat(log_msg, (), FormatDict(self._parent.locals))
        return log_msg, watch_results, _var_lookup


class LogActionResult(ActionResult):

    def __init__(self, action: 'LocationAction', log: str):
        self.action = action
        self.log = log

    def collect(self, ctx_id: str, logger: TracepointLogger, service: PushService) -> ActionCallback | None:
        logger.log_tracepoint(self.log, ctx_id, self.action.id)
        return None