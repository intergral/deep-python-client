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

"""Main entry for Deep Client."""

import inspect
import os

from deep import logging, version
from deep.api import Deep


def start(config=None) -> 'Deep':
    """
    Start DEEP.

    :param config: a custom config
    :return: the created Deep instance
    """
    if config is None:
        config = {}

    # we use the app root to shorten file paths for display
    if 'APP_ROOT' not in config:
        # if app root is not set then we use the folder in which the code that called us is in as the app root
        config['APP_ROOT'] = os.getenv("DEEP_APP_ROOT", None) or os.path.dirname(
            os.path.dirname(inspect.stack()[1].filename))

    from deep.config.config_service import ConfigService
    cfg = ConfigService(config)
    logging.init(cfg)

    logging.info("Deep Python Client [%s] (c) 2023 Intergral GmbH", version.__version__)

    deep = Deep(cfg)
    deep.start()
    return deep
