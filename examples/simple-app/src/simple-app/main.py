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

"""Example of using Deep with OTEl."""

import signal
import time

import deep
from deep.api.tracepoint.constants import FIRE_COUNT
from simple_test import SimpleTest


class GracefulKiller:
    """Ensure clean shutdown."""

    kill_now = False

    def __init__(self):
        """Crate new killer."""
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        """Exit example."""
        self.kill_now = True


def main():
    """Run the example."""
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
    _deep = deep.start({
        'SERVICE_URL': 'localhost:43315',
        'SERVICE_SECURE': 'False',
    })

    _deep.register_tracepoint("simple_test.py", 35, {FIRE_COUNT: '-1'})
    print("app running")
    main()
