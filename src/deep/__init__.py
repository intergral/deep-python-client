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

from deep import logging
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

    deep = Deep(cfg)
    deep.start()
    return deep
