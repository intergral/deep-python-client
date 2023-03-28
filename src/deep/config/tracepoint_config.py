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

import abc
import logging


class TracepointConfigService:
    """This service deals with new responses from the LongPoll"""
    def __init__(self) -> None:
        self._tracepoint_config = []
        self._current_hash = None
        self._last_update = 0
        self._task_handler = None
        self._listeners = []

    def update_no_change(self, ts):
        """
        This is called when the response says the config has not changed
        :param ts: the ts of the last poll, in ms
        """
        self._last_update = ts

    def update_new_config(self, ts, new_hash, new_config):
        """
        This is called when there is a change in the config, this will trigger a call to all listeners
        :param ts: the ts of the last poll, in ms
        :param new_hash: the new config hash
        :param new_config: the new config values
        """
        old_hash = self._current_hash
        old_config = self._tracepoint_config
        self._last_update = ts
        self._current_hash = new_hash
        self._tracepoint_config = new_config
        if self._task_handler is not None:
            future = self._task_handler.submit_task(self.update_listeners, self._last_update, old_hash,
                                                    self._current_hash, old_config, self._tracepoint_config)
            future.add_done_callback(lambda _: logging.debug("Completed processing new config %s", ts))

    def set_task_handler(self, task_handler):
        """Link in task handler"""
        self._task_handler = task_handler

    def update_listeners(self, ts, old_hash, current_hash, old_config, new_config):
        """This is called to update any listeners that the config has changed"""
        listeners_copy = self._listeners.copy()
        for listeners in listeners_copy:
            try:
                listeners.config_change(ts, old_hash, current_hash, old_config, new_config)
            except Exception:
                logging.exception("Error updating listener %s", listeners)

    def add_listener(self, listener):
        """Add a new listener to the config"""
        self._listeners.append(listener)

    @property
    def current_config(self):
        return self._tracepoint_config

    @property
    def current_hash(self):
        return self._current_hash


class ConfigUpdateListener(abc.ABC):
    """
    Class to describe a config listener
    """

    @abc.abstractmethod
    def config_change(self, ts, old_hash, current_hash, old_config, new_config):
        """
        Called when the config has changed
        :param ts: the ts of the new config
        :param old_hash: the old config hash
        :param current_hash: the new config hash
        :param old_config: the old config
        :param new_config: the new config
        """
        raise NotImplementedError
