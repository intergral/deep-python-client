import threading
import platform

from deep.api.attributes import BoundedAttributes
from deep.api.plugin import Plugin


class PythonPlugin(Plugin):
    def load_plugin(self):
        return BoundedAttributes(attributes={
            "python_version": platform.python_version(),
        })

    def collect_attributes(self):
        thread = threading.current_thread()

        return BoundedAttributes(attributes={
            'thread_name': thread.name
        })
