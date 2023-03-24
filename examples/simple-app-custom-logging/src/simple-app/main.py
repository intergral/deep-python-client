
import deep
import os

if __name__ == '__main__':
    deep.start({
        'SERVICE_URL': 'localhost:43315',
        'LOGGING_CONF': "%s/logging.conf" % os.path.dirname(os.path.realpath(__file__))
    })
    print("app running")
