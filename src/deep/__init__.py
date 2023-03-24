from deep import logging
from deep.api import Deep


def start(config=None):
    if config is None:
        config = {}

    from deep.config.config_service import Config
    cfg = Config(config)
    logging.init(cfg)

    deep = Deep(cfg)
    deep.start()
    return deep
