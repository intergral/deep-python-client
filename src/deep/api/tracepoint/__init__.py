#       Copyright (C) 2023  Intergral GmbH
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

"""Internal types for GRPC data."""

from .eventsnapshot import StackFrame, EventSnapshot, Variable, VariableId, WatchResult
from .tracepoint_config import TracePointConfig

__all__ = [TracePointConfig.__name__, StackFrame.__name__, EventSnapshot.__name__,
           Variable.__name__, WatchResult.__name__, VariableId.__name__]
