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
import signal
import time

import deep
from simple_test import SimpleTest


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


def main():
    killer = GracefulKiller()
    ts = SimpleTest("This is a test")
    while not killer.kill_now:
        try:
            ts.message(ts.new_id())
        except BaseException as e:
            print(e)
            ts.reset()

        time.sleep(0.1)


if __name__ == '__main__':
    deep.start()

    print("app running")
    main()
