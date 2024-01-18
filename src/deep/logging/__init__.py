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

"""Deep client logging api."""

import logging
import logging.config
import os


def warning(msg, *args, **kwargs):
    """
    Log a message at warning level.

    :param msg: the message to log
    :param args:  the args for the log
    :param kwargs: the kwargs
    """
    logging.getLogger("deep").warning(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """
    Log a message at info level.

    :param msg: the message to log
    :param args:  the args for the log
    :param kwargs: the kwargs
    """
    logging.getLogger("deep").info(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    """
    Log a message at debug level.

    :param msg: the message to log
    :param args:  the args for the log
    :param kwargs: the kwargs
    """
    logging.getLogger("deep").debug(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """
    Log a message at error level.

    :param msg: the message to log
    :param args:  the args for the log
    :param kwargs: the kwargs
    """
    logging.getLogger("deep").error(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    """
    Log a message with the exception data.

    :param msg: the message to log
    :param args:  the args for the log
    :param exc_info: include exc info in log
    :param kwargs: the kwargs
    """
    logging.getLogger("deep").exception(msg, *args, exc_info=exc_info, **kwargs)


def init(cfg=None):
    """
    Configure the deep log provider.

    :param cfg: the config for deep.
    """
    log_conf = "%s/logging.conf" % os.path.dirname(os.path.realpath(__file__))

    if cfg is not None and cfg.LOGGING_CONF:
        log_conf = cfg.LOGGING_CONF

    logging.config.fileConfig(fname=log_conf, disable_existing_loggers=False)
