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

"""Constant values used in tracepoint args."""

# Below are constants used in the configuration of a tracepoint

FIRE_COUNT = "fire_count"
"""The number of times this tracepoint should fire"""

WINDOW_START = "window_start"
"""The start of the time period this tracepoint can fire in"""

WINDOW_END = "window_end"
"""The end of the time period this tracepoint can fire in"""

FIRE_PERIOD = "fire_period"
"""The minimum time between successive triggers, in ms"""

CONDITION = "condition"
"""The condition that has to be 'truthy' for this tracepoint to fire"""

FRAME_TYPE = 'frame_type'
"""This is the key to indicate the frame collection type"""

STACK_TYPE = 'stack_type'
"""This is the key to indicate the stack collection type"""

SINGLE_FRAME_TYPE = 'single_frame'
"""Collect only the frame we are on"""

ALL_FRAME_TYPE = 'all_frame'
"""Collect from all available frames"""

NO_FRAME_TYPE = 'no_frame'
"""Collect on frame data"""

STACK = 'stack'
"""Collect the full stack"""

NO_STACK = 'no_stack'
"""Do not collect the stack data"""

LOG_MSG = 'log_msg'
"""The log message to interpolate at position of tracepoint"""

METHOD_NAME = "method_name"
"""This is the key for the arg that defines a method tracepoint."""

SPAN = "span"
"""This is the key for the arg that defines a span type."""

LINE = "line"
"""This is used for SPAN type. This type means we should wrap the method the tracepoint is in."""

METHOD = "method"
"""This is used for SPAN type. This type means we should only wrap the line the tracepoint is on."""

SNAPSHOT = "snapshot"
"""This is the key to determine the collection state of the snapshot."""

COLLECT = "collect"
"""This is the default collection type and tells Deep to collect and send the snapshot."""

NO_COLLECT = "no_collect"
"""This type tells Deep to not collect any data and not to send the snapshot."""

STAGE = "stage"
"""The stage this tracepoint is configured to trigger at."""

LINE_START = "line_start"
"""Line start stage"""
LINE_END = "line_end"
"""Line end stage"""
LINE_CAPTURE = "line_capture"
"""Line capture stage"""

LINE_STAGES = [LINE_CAPTURE, LINE_START, LINE_END]
"""All stages linked to lines."""

METHOD_START = "method_start"
"""Method start stage"""
METHOD_END = "method_end"
"""Method end stage"""
METHOD_CAPTURE = "method_capture"
"""Method capture stage"""

METHOD_STAGES = [METHOD_START, METHOD_CAPTURE, METHOD_END]
"""All stages linked to methods."""

WATCHES = "watches"
"""Key for watch config"""
