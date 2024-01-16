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

"""Service for customizing the tracepoint logging."""

import abc

from deep import logging


class TracepointLogger(abc.ABC):
    """
    This defines how a tracepoint logger should interact with Deep.

    This can be registered with Deep to provide customization to the way Deep will log dynamic log
    messages injected via tracepoints.
    """

    @abc.abstractmethod
    def log_tracepoint(self, log_msg: str, tp_id: str, ctx_id: str):
        """
        Log the dynamic log message.

        :param (str) log_msg: the log message to log
        :param (str) tp_id:  the id of the tracepoint that generated this log
        :param (str) snap_id: the is of the snapshot that was created by this tracepoint
        """
        pass


class DefaultLogger(TracepointLogger):
    """The default tracepoint logger used by Deep."""

    def log_tracepoint(self, log_msg: str, tp_id: str, ctx_id: str):
        """
        Log the dynamic log message.

        :param (str) log_msg: the log message to log
        :param (str) tp_id:  the id of the tracepoint that generated this log
        :param (str) snap_id: the is of the snapshot that was created by this tracepoint
        """
        logging.info(log_msg + " ctx=%s tracepoint=%s" % (ctx_id, tp_id))
