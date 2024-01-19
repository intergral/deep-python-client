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
from types import FrameType
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from deep.processor.context.trigger_context import TriggerContext


class ActionCallback:
    """A call back to 'close' an action."""

    @abc.abstractmethod
    def process(self, event: str, frame: FrameType, arg: any) -> bool:
        """
        Process a callback.

        :param event: the event
        :param frame: the frame data
        :param arg: the arg from settrace
        :return: True, to keep this callback until next match.
        """
        pass


class ActionResult(abc.ABC):
    """
    ActionResult represents the result of a trigger action.

    This could be the snapshot to ship, logs to process or a span to close.
    """

    @abc.abstractmethod
    def process(self, ctx: 'TriggerContext') -> Optional[ActionCallback]:
        """
        Process this result.

        :param ctx: the triggering context

        :return: an action callback if we need to do something at the 'end', or None
        """
        pass
