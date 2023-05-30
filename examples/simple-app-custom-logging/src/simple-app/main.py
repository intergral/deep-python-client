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

import os

import deep

if __name__ == '__main__':
    deep.start({
        'SERVICE_URL': 'localhost:43315',
        'LOGGING_CONF': "%s/logging.conf" % os.path.dirname(os.path.realpath(__file__))
    })
    print("app running")
