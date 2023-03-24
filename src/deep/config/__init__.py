import os

from .config_service import Config

'''The path to the logging config file to use'''
LOGGING_CONF = os.getenv('DEEP_LOGGING_CONF', None)

POLL_TIMER = os.getenv('DEEP_POLL_TIMER', 10)  # time in seconds

SERVICE_URL = os.getenv('DEEP_SERVICE_URL', 'deep:43315')
SERVICE_SECURE = os.getenv('SERVICE_SECURE', True)
SERVICE_AUTH_PROVIDER = os.getenv('DEEP_SERVICE_AUTH_PROVIDER', None)
SERVICE_USERNAME = os.getenv('DEEP_SERVICE_USERNAME', None)
SERVICE_PASSWORD = os.getenv('DEEP_SERVICE_PASSWORD', None)
# Config items can be functions
# def SERVICE_URL():
#     return os.getenv('SERVICE_URL', 'localhost:50051')
