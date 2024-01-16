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
import os
from importlib import import_module
from typing import Tuple

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.utils import str2bool

DEEP_PLUGINS = [
    'deep.api.plugin.otel.OTelPlugin',
    'deep.api.plugin.python.PythonPlugin',
]


def __plugin_generator(configured):
    for plugin in configured:
        try:
            module, cls = plugin.rsplit(".", 1)
            yield getattr(import_module(module), cls)
            logging.debug('Did import default integration %s', plugin)
        except (DidNotEnable, SyntaxError) as e:
            logging.debug(
                "Did not import default integration %s: %s", plugin, e
            )


def load_plugins() -> Tuple[list['Plugin'], BoundedAttributes]:
    """
    Load all the deep plugins.

    Attempt to load each plugin, if successful merge a attributes list of each plugin.

    :return: the loaded plugins and attributes.
    """
    bounded_attributes = BoundedAttributes(immutable=False)
    loaded = []
    for plugin in __plugin_generator(DEEP_PLUGINS):
        try:
            plugin_instance = plugin()
            if not plugin_instance.is_active():
                logging.debug("Plugin %s is not active.", plugin_instance.name)
                continue
            attributes = plugin_instance.load_plugin()
            if attributes is not None:
                bounded_attributes.merge_in(attributes)
            loaded.append(plugin_instance)
        except Exception as e:
            logging.debug("Could not load plugin %s: %s", plugin, e)
    return loaded, bounded_attributes


class Plugin(abc.ABC):
    """
    A deep Plugin.

    This type defines a plugin for deep, these plugins allow for extensions to how deep decorates data.
    """

    def __init__(self, name=None):
        """Create a new."""
        super(Plugin, self).__init__()
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

        Check the value of the environment value of the module name + class name. It set to
        'false' this plugin is not active.
        """
        getenv = os.getenv("{0}.{1}".format(self.__class__.__module__, self.__class__.__name__), 'True')
        return str2bool(getenv)

    @abc.abstractmethod
    def load_plugin(self) -> BoundedAttributes:
        """
        Load the plugin.

        :return: any values to attach to the client resource.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def collect_attributes(self) -> BoundedAttributes:
        """
        Collect attributes to attach to snapshot.

        :return: the attributes to attach.
        """
        raise NotImplementedError()


class DidNotEnable(Exception):
    """
    Raised when failed to load plugin.

    The plugin could not be enabled due to a trivial user error like
    `otel` not being installed for the `OTelPlugin`.
    """


__all__ = [Plugin.__name__, DidNotEnable.__name__]
