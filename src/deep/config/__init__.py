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

"""
Config values for deep.

Here we have the initial values for the config, there can be set as either static values, environment values
 or functions.
"""

import os
import sys

from .config_service import ConfigService  # noqa: F401

LOGGING_CONF = os.getenv('DEEP_LOGGING_CONF', None)
'''The path to the logging config file to use'''

POLL_TIMER = os.getenv('DEEP_POLL_TIMER', 10)
"""The time in seconds to wait between each poll (default: 10)"""

SERVICE_URL = os.getenv('DEEP_SERVICE_URL', 'deep:43315')
"""The URL for the service to connect to (default: deep:43315)"""

SERVICE_SECURE = os.getenv('DEEP_SERVICE_SECURE', 'True')
"""Is the service secured, should we connect with TLS or not (default: True)"""

SERVICE_AUTH_PROVIDER = os.getenv('DEEP_SERVICE_AUTH_PROVIDER', None)
"""The Auth provider to use for the service (default: None)"""

APP_ROOT = ""
"""App root sets the prefix that can be removed to generate shorter file names. This value is calculated."""

PLUGINS = []
"""User definable plugins."""


# noinspection PyPep8Naming
def IN_APP_INCLUDE():
    """
    Get the included app packages.

    The packages to mark as in app packages. (default: ''). Must be a command (,) seperated list.
    """
    user_defined = os.getenv('DEEP_IN_APP_INCLUDE', None)
    if user_defined is None:
        return []
    if ',' in user_defined:
        return user_defined.split(',')
    return [user_defined]


# noinspection PyPep8Naming
def IN_APP_EXCLUDE():
    """
    Get the exclude app packages.

    The packages to mark as NOT in app packages. (default: ''). Must be a command (,) seperated list.
    """
    user_defined = os.getenv('DEEP_IN_APP_EXCLUDE', None)
    if user_defined is None:
        user_defined = []
    else:
        if ',' in user_defined:
            user_defined = user_defined.split(',')
        user_defined = [user_defined]

    prefix = sys.exec_prefix
    user_defined.append(prefix)

    return user_defined
