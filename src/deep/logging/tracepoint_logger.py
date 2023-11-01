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
import abc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from deep.config import ConfigService

from deep import logging


class TracepointLogger(abc.ABC):

    @abc.abstractmethod
    def log_tracepoint(self, log_msg: str, tp_id: str, snap_id: str):
        pass


class DefaultLogger(TracepointLogger):
    def __init__(self, _config: 'ConfigService'):
        self._config = _config

    def log_tracepoint(self, log_msg: str, tp_id: str, snap_id: str):
        logging.info(log_msg + " snapshot=%s tracepoint=%s" % (snap_id, tp_id))
