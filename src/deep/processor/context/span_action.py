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

"""Handling for span actions."""
from types import FrameType
from typing import Optional, TYPE_CHECKING

from deep.processor.context.action_context import ActionContext
from deep.processor.context.action_results import ActionResult, ActionCallback

if TYPE_CHECKING:
    from deep.processor.context.trigger_context import TriggerContext


class SpanActionCallback(ActionCallback):
    """Action callback to close created spans."""

    def __init__(self, spans):
        """Create callback."""
        self.__spans = spans

    def process(self, event: str, frame: FrameType, arg: any) -> bool:
        """
        Process a callback.

        :param event: the event
        :param frame: the frame data
        :param arg: the arg from settrace
        :return: True, to keep this callback until next match.
        """
        for span in self.__spans:
            span.close()
        return False


class SpanResult(ActionResult):
    """Action result to map to callback."""

    def __init__(self, spans):
        """Create result."""
        self.__spans = spans

    def process(self, ctx: 'TriggerContext') -> Optional[ActionCallback]:
        """
        Process this result.

        :param ctx: the triggering context

        :return: an action callback if we need to do something at the 'end', or None
        """
        return SpanActionCallback(self.__spans)


class SpanActionContext(ActionContext):
    """Action for spans."""

    def can_trigger(self) -> bool:
        """
        Check if the action can trigger.

        If we do not have a span processor enabled, then skip this action.
        :return: True, if the trigger can be triggered.
        """
        if self.trigger_context.config.has_span_processor:
            return super().can_trigger()
        return False

    def _process_action(self):
        name = self._span_name
        if name is None:
            return

        spans = []

        for span_processor in self.trigger_context.config.span_processors:
            span = span_processor.create_span(name)
            if span:
                spans.append(span)

        if len(spans) > 0:
            self.trigger_context.attach_result(SpanResult(spans))

    @property
    def _span_name(self):
        location = self.location_action.location
        if location:
            return location.name
