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

"""A collection of util functions to perform common or repeated actions."""

import logging
import time
from threading import Event, Thread


def snapshot_id_as_hex_str(snapshot_id):
    """Convert a snapshot if to a hex string."""
    return snapshot_id.to_bytes(16, 'big').hex()


def time_ms():
    """Get the current epoch time in milliseconds."""
    return int(round(time.time() * 1000))


def time_ns():
    """Get the current epoch time in nanoseconds."""
    return time.time_ns()


def str2bool(string):
    """
    Convert a string to a boolean.

    :param string: the string to convert
    :return: True, if string is yes, true, t or 1. (case-insensitive)
    """
    return string.lower() in ("yes", "true", "t", "1", "y")


class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""

    def __init__(self, name, interval, function, *args, **kwargs):
        """
        Create a new RepeatTimer.

        :param name: the name of the timer
        :param interval: the time in seconds between each execution
        :param function: the function to repeat
        :param args: the arguments for the function
        :param kwargs: the kwargs for the function
        """
        self.name = name
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start_ts = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target, name=self.name)
        self.thread.daemon = True

    def start(self):
        """Start the thread to run the timer."""
        self.thread.start()

    def stop(self):
        """Stop and shutdown the timer."""
        self.event.set()
        self.thread.join()

    def _target(self):
        while not self.event.wait(self._time):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception:
                logging.exception(
                    "Repeated function (%s) failed, will retry in %s seconds." % (self.name, self.interval))

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start_ts) % self.interval)
