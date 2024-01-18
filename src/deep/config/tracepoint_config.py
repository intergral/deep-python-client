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

"""Maintain the current config of the tracepoints."""

import abc
import logging
import uuid
from typing import Dict, List, TYPE_CHECKING

from deep.api.tracepoint.tracepoint_config import MetricDefinition

from deep.api.tracepoint.trigger import build_trigger

if TYPE_CHECKING:
    from deep.api.tracepoint.trigger import Trigger


class ConfigUpdateListener(abc.ABC):
    """Class to describe a config listener."""

    @abc.abstractmethod
    def config_change(self, ts: int, old_hash: str, current_hash: str, old_config: List['Trigger'],
                      new_config: List['Trigger']):
        """
        Process an update to the tracepoint config.

        :param ts: the ts of the new config
        :param old_hash: the old config hash
        :param current_hash: the new config hash
        :param old_config: the old config
        :param new_config: the new config
        """
        raise NotImplementedError


class TracepointConfigService:
    """This service deals with new responses from the LongPoll."""

    def __init__(self) -> None:
        """Create new tracepoint config service."""
        self._custom: List['Trigger'] = []
        self._tracepoint_config: List['Trigger'] = []
        self._current_hash = None
        self._last_update = 0
        self._task_handler = None
        self._listeners: List[ConfigUpdateListener] = []

    def update_no_change(self, ts):
        """
        Update no change detected.

        This is called when the response says the config has not changed

        :param ts: the ts of the last poll, in ms
        """
        self._last_update = ts

    def update_new_config(self, ts: int, new_hash: str, new_config: List['Trigger']):
        """
        Update to the new config.

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
        self.__trigger_update(old_hash, old_config)

    def __trigger_update(self, old_hash, old_config):
        ts = self._last_update
        if self._task_handler is not None:
            future = self._task_handler.submit_task(self.update_listeners, self._last_update, old_hash,
                                                    self._current_hash, old_config, self._tracepoint_config)
            future.add_done_callback(lambda _: logging.debug("Completed processing new config %s", ts))

    def set_task_handler(self, task_handler):
        """
        Set the task handler to use.

        :param task_handler: the taskhandler
        """
        self._task_handler = task_handler

    def update_listeners(self, ts: int, old_hash: str, current_hash: str, old_config: List['Trigger'],
                         new_config: List['Trigger']):
        """
        Update the registered listeners.

        This is called to update any listeners that the config has changed

        :param ts: the ts of the update
        :param old_hash: the old hash
        :param current_hash: the new hash value
        :param old_config: the old config
        :param new_config: the new config
        """
        listeners_copy = self._listeners.copy()
        for listeners in listeners_copy:
            try:
                listeners.config_change(ts, old_hash, current_hash, old_config, new_config + self._custom)
            except Exception:
                logging.exception("Error updating listener %s", listeners)

    def add_listener(self, listener: ConfigUpdateListener):
        """
        Add a new listener to the config.

        :param listener: the listener to add
        """
        self._listeners.append(listener)

    @property
    def current_config(self) -> List['Trigger']:
        """
        The current tracepoint config.

        :return: the config
        """
        return self._tracepoint_config

    @property
    def current_hash(self) -> str:
        """
        The current hash.

        The hash is updated only when the config is changed. It is used by the server and client to
        reduce the number of updates.

        :return: the current hash.
        """
        return self._current_hash

    def add_custom(self, path: str, line: int, args: Dict[str, str], watches: List[str],
                   metrics: List[MetricDefinition]) -> str:
        """
        Crate a new tracepoint from the input.

        :param path: the source file name
        :param line: the source line number
        :param args: the tracepoint args
        :param watches: the tracepoint watches
        :param metrics: the tracepoint metrics
        :return: the new TracePointConfig
        """
        config = build_trigger(str(uuid.uuid4()), path, line, args, watches, metrics)
        self._custom.append(config)
        self.__trigger_update(None, None)
        return config.id

    def remove_custom(self, _id: str):
        """
        Remove a custom tracepoint config.

        :param _id: the id of the config to remove
        """
        for idx, cfg in enumerate(self._custom):
            if cfg.id == _id:
                del self._custom[idx]
                self.__trigger_update(None, None)
                return
