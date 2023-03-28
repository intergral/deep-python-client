#     Copyright 2023 Intergral GmbH
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

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
