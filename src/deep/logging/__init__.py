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

import logging
import logging.config
import os


def warning(msg, *args, **kwargs):
    logging.getLogger("deep").warning(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    logging.getLogger("deep").info(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    logging.getLogger("deep").debug(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    logging.getLogger("deep").debug(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    logging.getLogger("deep").exception(msg, *args, exc_info=exc_info, **kwargs)


def init(cfg):
    log_conf = cfg.LOGGING_CONF or "%s/logging.conf" % os.path.dirname(os.path.realpath(__file__))
    logging.config.fileConfig(fname=log_conf, disable_existing_loggers=False)
