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

import logging
import threading
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor


class IllegalStateException(BaseException):
    pass


class TaskHandler:
    def __init__(self):
        self._pool = ThreadPoolExecutor(max_workers=2)
        self._pending = {}
        self._job_id = 0
        self._lock = threading.Lock()
        self._open = True

    def _next_id(self):
        with self._lock:
            self._job_id += 1
            next_id = self._job_id
        return next_id

    def check_open(self):
        if not self._open:
            raise IllegalStateException

    def submit_task(self, task, *args) -> Future:
        self.check_open()
        next_id = self._next_id()
        # there is an at exit in threading that prevents submitting tasks after shutdown, but no api to check this
        future = self._pool.submit(task, *args)
        self._pending[next_id] = future

        # cannot use 'del' in lambda: https://stackoverflow.com/a/41953232/5151254
        def callback(future: Future):
            if future.exception() is not None:
                logging.exception("Submitted task failed %s", task)
            if next_id in self._pending:
                del self._pending[next_id]

        future.add_done_callback(callback)
        return future

    def flush(self):
        self._open = False
        if len(self._pending) > 0:
            for key in dict(self._pending).keys():
                get = self._pending.get(key)
                if get is not None:
                    self._pending[key].result(10)
