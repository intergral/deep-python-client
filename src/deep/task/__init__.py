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
