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

import time

from base_test import BaseTest


class SimpleTest(BaseTest):

    def __init__(self, test_name) -> None:
        super().__init__()
        self._started_at = round(time.time() * 1000)
        self.__cnt = 0
        self.char_counter = {}
        self.test_name = test_name
        self.max_executions = self.next_max()

    def message(self, uuid):
        print("%s:%s" % (self.__cnt, uuid))
        self.__cnt += 1
        self.check_end(self.__cnt, self.max_executions)

        info = self.make_char_count_map(uuid)
        self.merge(self.char_counter, info)
        if self.__cnt % 30 == 0:
            self.dump()

    def merge(self, char_counter, new_info):

        for key in new_info:
            new_val = new_info[key]

            if key not in char_counter:
                char_counter[key] = new_val
            else:
                char_counter[key] = new_val + char_counter[key]

    def dump(self):
        print(self.char_counter)
        self.char_counter = {}

    def check_end(self, value, max_executions):
        if value > max_executions:
            raise Exception("Hit max executions %s %s " % (value, max_executions))

    def __str__(self) -> str:
        return self.__class__.__name__ + ":" + self.test_name + ":" + str(self._started_at)

    def reset(self):
        self.__cnt = 0
        self.max_executions = self.next_max()
