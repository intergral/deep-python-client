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

"""Simple example showing usage with OTEL."""

import signal
import time

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)

import deep
from deep.api.tracepoint.constants import METHOD_NAME, SPAN, METHOD, FIRE_COUNT, SNAPSHOT, NO_COLLECT
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
        with trace.get_tracer(__name__).start_as_current_span("loop"):
            with trace.get_tracer(__name__).start_as_current_span("loop-inner"):
                try:
                    ts.message(ts.new_id())
                except BaseException as e:
                    print(e)
                    ts.reset()

                time.sleep(0.1)


if __name__ == '__main__':
    resource = Resource(attributes={
        SERVICE_NAME: "your-service-name"
    })

    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831
    )

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(jaeger_exporter))
    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    _deep = deep.start({
        'SERVICE_URL': 'localhost:43315',
        'SERVICE_SECURE': 'False',
        'POLL_TIMER': 10000
    })

    tracepoint = _deep.register_tracepoint("simple_test.py", -1,
                                           {METHOD_NAME: 'message', SPAN: METHOD, FIRE_COUNT: '-1',
                                            SNAPSHOT: NO_COLLECT})

    print("app running")
    main()
