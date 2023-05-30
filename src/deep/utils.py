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

import logging
import time
from threading import Event, Thread


def snapshot_id_as_hex_str(snapshot_id):
    """"Convert a snapshot if to a hex string."""
    return snapshot_id.to_bytes(16, 'big').hex()


def time_ms():
    """Get the current epoch time in milliseconds."""
    return int(round(time.time() * 1000))


def time_ns():
    """Get the current epoch time in nanoseconds."""
    return time.time_ns()


def reduce_list(key, update_value, default_value, lst):
    """Reduce a list to a dict.

    key :: list_item -> dict_key
    update_value :: key * existing_value -> updated_value
    default_value :: initial value passed to update_value
    lst :: The list

    default_value comes before l. This is different from functools.reduce,
    because functools.reduce's order is wrong.
    """
    d = {}
    for k in lst:
        j = key(k)
        d[j] = update_value(k, d.get(j, default_value))
    return d


def str2bool(string):
    """
    Convert a string to a boolean

    :param string: the string to convert
    :return: True, if string is yes, true, t or 1. (case insensitive)
    """
    return string.lower() in ("yes", "true", "t", "1")


class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""

    def __init__(self, name, interval, function, *args, **kwargs):
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
        self.thread.start()

    def stop(self):
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
