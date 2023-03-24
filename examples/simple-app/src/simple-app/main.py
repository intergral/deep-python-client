from time import sleep

import deep

if __name__ == '__main__':
    deep.start({
        'SERVICE_URL': 'localhost:43315',
        'SERVICE_SECURE': False,
        'SERVICE_AUTH_PROVIDER': 'deep.api.auth.BasicAuthProvider',
        'SERVICE_USERNAME': 'bob',
        'SERVICE_PASSWORD': 'obo'
    })
    while True:
        print("app running")
        sleep(120)
