import time

from base_test import BaseTest


class SimpleTest(BaseTest):

    def __init__(self, test_name) -> None:
        super().__init__()
        self.started_at = round(time.time() * 1000)
        self.cnt = 0
        self.char_counter = {}
        self.test_name = test_name
        self.max_executions = self.next_max()

    def message(self, uuid):
        print("%s:%s" % (self.cnt, uuid))
        self.cnt += 1
        self.check_end(self.cnt, self.max_executions)

        info = self.make_char_count_map(uuid)
        self.merge(self.char_counter, info)
        if self.cnt % 30 == 0:
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
        return self.__class__.__name__ + ":" + self.test_name + ":" + str(self.started_at)

    def reset(self):
        self.cnt = 0
        self.max_executions = self.next_max()
