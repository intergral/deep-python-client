#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import logging
import time
from threading import Event, Thread


def time_ms():
    return int(round(time.time() * 1000))


def time_ns():
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
