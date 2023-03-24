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
