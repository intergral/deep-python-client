import time

from simple_test import SimpleTest

import deep


def main():
    ts = SimpleTest("This is a test")
    while True:
        try:
            ts.message(ts.new_id())
        except Exception as e:
            print(e)
            ts.reset()

        time.sleep(0.1)


if __name__ == '__main__':
    deep.start({
        'SERVICE_URL': 'localhost:43315',
        'SERVICE_SECURE': False,
        'SERVICE_AUTH_PROVIDER': 'deep.api.auth.BasicAuthProvider',
        'SERVICE_USERNAME': 'bob',
        'SERVICE_PASSWORD': 'obo'
    })

    print("app running")
    main()
