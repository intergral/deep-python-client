
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
