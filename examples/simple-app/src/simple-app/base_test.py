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

import random
import uuid


class BaseTest:
    """A basic test that is used in examples."""

    def new_id(self):
        """Create new id."""
        return str(uuid.uuid4())

    def next_max(self):
        """Create new random max."""
        return random.randint(1, 101)

    def make_char_count_map(self, in_str):
        """Create char count map."""
        res = {}

        for i in range(0, len(in_str)):
            c = in_str[i]
            if c not in res:
                res[c] = 0
            else:
                res[c] = res[c] + 1
        return res
