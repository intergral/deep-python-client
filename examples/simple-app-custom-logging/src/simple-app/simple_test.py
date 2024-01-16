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

"""A simple test object for examples."""

import time

from base_test import BaseTest


class SimpleTest(BaseTest):
    """A basic test that is used in examples."""

    def __init__(self, test_name):
        """Create new test object."""
        super().__init__()
        self._started_at = round(time.time() * 1000)
        self.__cnt = 0
        self.char_counter = {}
        self.test_name = test_name
        self.max_executions = self.next_max()

    def message(self, uuid):
        """Print message to console."""
        print("%s:%s" % (self.__cnt, uuid))
        self.__cnt += 1
        self.check_end(self.__cnt, self.max_executions)

        info = self.make_char_count_map(uuid)
        self.merge(self.char_counter, info)
        if self.__cnt % 30 == 0:
            self.dump()

    def merge(self, char_counter, new_info):
        """Merge captured data."""
        for key in new_info:
            new_val = new_info[key]

            if key not in char_counter:
                char_counter[key] = new_val
            else:
                char_counter[key] = new_val + char_counter[key]

    def dump(self):
        """Dump message to console."""
        print(self.char_counter)
        self.char_counter = {}

    def check_end(self, value, max_executions):
        """Check if we are at end."""
        if value > max_executions:
            raise Exception("Hit max executions %s %s " % (value, max_executions))

    def __str__(self) -> str:
        """Represent this as a string."""
        return self.__class__.__name__ + ":" + self.test_name + ":" + str(self._started_at)

    def reset(self):
        """Reset the count."""
        self.__cnt = 0
        self.max_executions = self.next_max()
