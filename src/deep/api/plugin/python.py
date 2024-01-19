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
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.#
#      You should have received a copy of the GNU Affero General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Simple plugin for deep, decorating some python information."""

import platform
import threading
from typing import Optional

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.api.plugin import ResourceProvider, TracepointLogger, SnapshotDecorator
from deep.api.resource import Resource
from deep.processor.context.action_context import ActionContext


class PythonPlugin(ResourceProvider, SnapshotDecorator, TracepointLogger):
    """
    Deep python plugin.

    This plugin provides the python version to the resource, and the thread name to the attributes.
    """

    def decorate(self, context: ActionContext) -> Optional[BoundedAttributes]:
        """
        Decorate a snapshot with additional data.

        :param context: the action context for this action

        :return: the additional attributes to attach
        """
        thread = threading.current_thread()

        return BoundedAttributes(attributes={
            'thread_name': thread.name
        })

    def resource(self) -> Optional[Resource]:
        """
        Provide resource.

        :return: the provided resource
        """
        return Resource.create({
            "python_version": platform.python_version(),
        })

    def log_tracepoint(self, log_msg: str, tp_id: str, ctx_id: str):
        """
        Log the dynamic log message.

        :param (str) log_msg: the log message to log
        :param (str) tp_id:  the id of the tracepoint that generated this log
        :param (str) ctx_id: the id of the context that was created by this tracepoint
        """
        logging.info(log_msg + " ctx=%s tracepoint=%s" % (ctx_id, tp_id))
