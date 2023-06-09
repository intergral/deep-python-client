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

import abc
import os
from importlib import import_module

from deep import logging
from deep.api.attributes import BoundedAttributes
from deep.utils import str2bool

DEEP_PLUGINS = [
    'deep.api.plugin.otel.OTelPlugin',
    'deep.api.plugin.python.PythonPlugin',
]


def plugin_generator(configured):
    for plugin in configured:
        try:
            module, cls = plugin.rsplit(".", 1)
            yield getattr(import_module(module), cls)
            logging.debug('Did import default integration %s', plugin)
        except (DidNotEnable, SyntaxError) as e:
            logging.debug(
                "Did not import default integration %s: %s", plugin, e
            )


def load_plugins():
    bounded_attributes = BoundedAttributes(immutable=False)
    loaded = []
    for plugin in plugin_generator(DEEP_PLUGINS):
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
    This type defines a plugin for deep, these plugins allow for extensions to how deep decorates data.
    """

    def __init__(self, name=None):
        super(Plugin, self).__init__()
        if name is None:
            self._name = self.__class__.__name__
        else:
            self._name = name

    @property
    def name(self):
        return self._name

    def is_active(self):
        # type: ()-> bool
        getenv = os.getenv("{0}.{1}".format(self.__class__.__module__, self.__class__.__name__), 'True')
        return str2bool(getenv)

    @abc.abstractmethod
    def load_plugin(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def collect_attributes(self) -> BoundedAttributes:
        raise NotImplementedError()


class DidNotEnable(Exception):
    """
    The plugin could not be enabled due to a trivial user error like
    `otel` not being installed for the `OTelPlugin`.
    """


__all__ = [Plugin.__name__, DidNotEnable.__name__]
