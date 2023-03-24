import os
import sys

from .config_service import ConfigService

'''The path to the logging config file to use'''
LOGGING_CONF = os.getenv('DEEP_LOGGING_CONF', None)

POLL_TIMER = os.getenv('DEEP_POLL_TIMER', 10)  # time in seconds

SERVICE_URL = os.getenv('DEEP_SERVICE_URL', 'deep:43315')
SERVICE_SECURE = os.getenv('SERVICE_SECURE', True)
SERVICE_AUTH_PROVIDER = os.getenv('DEEP_SERVICE_AUTH_PROVIDER', None)
SERVICE_USERNAME = os.getenv('DEEP_SERVICE_USERNAME', None)
SERVICE_PASSWORD = os.getenv('DEEP_SERVICE_PASSWORD', None)


def IN_APP_INCLUDE():
    user_defined = os.getenv('DEEP_IN_APP_INCLUDE', None)
    if user_defined is None:
        user_defined = []
    return user_defined


def IN_APP_EXCLUDE():
    user_defined = os.getenv('DEEP_IN_APP_INCLUDE', None)
    if user_defined is None:
        user_defined = []

    prefix = sys.exec_prefix
    user_defined.append(prefix)

    # path_to_us = Path(__file__)
    # while path_to_us.name != "site-packages" and len(path_to_us.parents) > 0:
    #     path_to_us = path_to_us.parent
    # if len(path_to_us.parents) > 0 != "/":
    #     user_defined.append(str(path_to_us.parent.absolute()))
    return user_defined

# Config items can be functions
# def SERVICE_URL():
#     return os.getenv('SERVICE_URL', 'localhost:50051')
