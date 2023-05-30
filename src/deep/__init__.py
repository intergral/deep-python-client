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

from deep import logging, version
from deep.api import Deep


def start(config=None):
    """
    Start DEEP.
    :param config: a custom config
    :return: the created Deep instance
    """
    if config is None:
        config = {}

    from deep.config.config_service import ConfigService
    cfg = ConfigService(config)
    logging.init(cfg)

    logging.info("Deep Python Client [%s] (c) 2023 Intergral GmbH", version.__version__)

    deep = Deep(cfg)
    deep.start()
    return deep
