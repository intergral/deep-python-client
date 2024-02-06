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

"""Load and handle plugins."""

import abc
from importlib import import_module
from typing import TYPE_CHECKING, Optional, TypeVar, List

from deep.api.resource import Resource
from deep.processor.context.action_context import ActionContext

if TYPE_CHECKING:
    from deep.config import ConfigService

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.utils import str2bool

DEEP_PLUGINS = [
    'deep.api.plugin.otel.OTelPlugin',
    'deep.api.plugin.python.PythonPlugin',
    'deep.api.plugin.metric.prometheus_metrics.PrometheusPlugin',
    'deep.api.plugin.metric.otel_metrics.OTelMetrics',
]
"""System provided default plugins."""


def __plugin_generator(configured):
    for plugin in configured:
        try:
            module, cls = plugin.rsplit(".", 1)
            yield getattr(import_module(module), cls)
            logging.debug('Did import integration %s', plugin)
        except (DidNotEnable, Exception) as e:
            logging.debug(
                "Did not import integration %s: %s", plugin, e
            )


def load_plugins(config: 'ConfigService', custom=None) -> List['Plugin']:
    """
    Load all the deep plugins.

    Attempt to load each plugin, if successful merge an attributes list of each plugin.

    :return: the loaded plugins and attributes.
    """
    if custom is None:
        custom = []
    loaded = []
    for plugin in __plugin_generator(DEEP_PLUGINS + custom):
        try:
            plugin_instance = plugin(config=config)
            if not plugin_instance.is_active():
                logging.debug("Plugin %s is not active.", plugin_instance.name)
                continue
            loaded.append(plugin_instance)
        except Exception as e:
            logging.debug("Could not load plugin %s: %s", plugin, e)

    loaded.sort(key=lambda pl: pl.order() or 0)
    return loaded


class Plugin(abc.ABC):
    """
    A deep Plugin.

    This type defines a plugin for deep, these plugins allow for extensions to how deep decorates data.
    """

    def __init__(self, name: str = None, config: 'ConfigService' = None):
        """
        Create a new plugin.

        :param name: the name of the plugin (default to class name)
        :param config: the deep config service
        """
        super(Plugin, self).__init__()
        self.config = config
        if name is None:
            self._name = self.__class__.__name__
        else:
            self._name = name

    @property
    def name(self):
        """The name of the plugin."""
        return self._name

    def is_active(self) -> bool:
        """
        Is the plugin active.

        Check the value of the config element plugin_{name}. If it is set to
        'False' this plugin is not active.
        """
        attr = getattr(self.config, f'plugin_{self.name}'.upper(), 'True')
        if attr is None:
            return True
        return str2bool(attr)

    def shutdown(self):
        """Clean up and shutdown the plugin."""
        pass

    def order(self) -> int:
        """
        Order of precedence when multiple versions of providers are available.

        Order=1 will run after a provider with order=0.

        :return: the provider order
        """
        return 0


PLUGIN_TYPE = TypeVar('PLUGIN_TYPE', bound=Plugin)


class ResourceProvider(Plugin, abc.ABC):
    """Implement this to have the plugin provide resource attributes to Deep."""

    @abc.abstractmethod
    def resource(self) -> Optional[Resource]:
        """
        Provide resource.

        :return: the provided resource
        """
        pass


class SnapshotDecorator(Plugin, abc.ABC):
    """Implement this to decorate collected snapshots with attributes."""

    @abc.abstractmethod
    def decorate(self, context: ActionContext) -> Optional[BoundedAttributes]:
        """
        Decorate a snapshot with additional data.

        :param context: the action context for this action

        :return: the additional attributes to attach
        """
        pass


class TracepointLogger(Plugin, abc.ABC):
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
        :param (str) ctx_id: the id of the context that was created by this tracepoint
        """
        pass


class DidNotEnable(Exception):
    """
    Raised when failed to load plugin.

    The plugin could not be enabled due to a trivial user error like
    `otel` not being installed for the `OTelPlugin`.
    """


__all__ = [Plugin.__name__, DidNotEnable.__name__]
