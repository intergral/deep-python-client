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

"""Handler results of actions."""

import abc
from typing import Optional

from deep.logging.tracepoint_logger import TracepointLogger
from deep.push import PushService


class ActionCallback:
    """A call back to 'close' an action."""

    def process(self, frame, event) -> bool:
        """
        Process a callback.

        :param frame: the frame data
        :param event: the event
        :return: True, to keep this callback until next match.
        """
        pass


class ActionResult(abc.ABC):
    """
    ActionResult represents the result of a trigger action.

    This could be the snapshot to ship, logs to process or a span to close.
    """

    @abc.abstractmethod
    def process(self, ctx_id: str, logger: TracepointLogger, service: PushService) -> Optional[ActionCallback]:
        """
        Process this result.

        Either log or ship the collected data to an endpoint.

        :param ctx_id: the triggering context id
        :param logger: the log service
        :param service:the push service
        :return: an action callback if we need to do something at the 'end', or None
        """
        pass
