#       Copyright (C) 2024  Intergral GmbH
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

"""Simple example showing usage with prometheus metrics."""

import signal
import time

from prometheus_client import Summary, start_http_server

import deep
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


# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')


# Decorate function with metric.
@REQUEST_TIME.time()
def process_request(t):
    """
    Sleep.

    A dummy function that takes some time.
    """
    time.sleep(t)


if __name__ == '__main__':
    start_http_server(8000)
    d = deep.start({
        'SERVICE_URL': 'localhost:43315',
        'SERVICE_SECURE': 'False',
    })

    d.register_tracepoint("simple_test.py", 31)

    print("app running")
    main()
