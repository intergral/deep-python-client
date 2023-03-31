
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

import random
import uuid


class BaseTest:

    def new_id(self):
        return str(uuid.uuid4())

    def next_max(self):
        return random.randint(1, 101)

    def make_char_count_map(self, in_str):
        res = {}

        for i in range(0, len(in_str)):
            c = in_str[i]
            if c not in res:
                res[c] = 0
            else:
                res[c] = res[c] + 1
        return res
