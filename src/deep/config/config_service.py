from typing import Any

from deep import logging
from deep.api.resource import Resource
from deep.config.tracepoint_config import TracepointConfigService


class ConfigService:
    def __init__(self, custom):
        self.custom = custom
        self._resource = None
        self._tracepoint_config = TracepointConfigService()

    def __getattribute__(self, name: str) -> Any:
        attr = None
        try:
            attr = super().__getattribute__(name)
        except AttributeError:

            if self.custom is not None and name in self.custom:
                attr = self.custom[name]

            if attr is None:
                from deep import config
                has_attr = hasattr(config, name)
                if not has_attr:
                    logging.warning("Unrecognised config key: %s", name)
                    return None
                attr = getattr(config, name, None)

            if callable(attr):
                return attr()

        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

    def set_task_handler(self, task_handler):
        self._tracepoint_config.set_task_handler(task_handler)

    @property
    def resource(self) -> Resource:
        return self._resource

    @resource.setter
    def resource(self, new_resource):
        self._resource = new_resource

    @property
    def tracepoints(self) -> TracepointConfigService:
        return self._tracepoint_config

    def add_listener(self, listener):
        self._tracepoint_config.add_listener(listener)
