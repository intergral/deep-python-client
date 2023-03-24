class TracepointConfigService:
    def __init__(self) -> None:
        self._tracepoint_config = []
        self._current_hash = None
        self._last_update = 0

    @property
    def current_hash(self):
        return self._current_hash

    def update_no_change(self, ts):
        self._last_update = ts

    def update_new_config(self, ts, new_hash, new_config):
        self._last_update = ts
        self._current_hash = new_hash
        self._tracepoint_config = new_config

    @property
    def current_config(self):
        return self._tracepoint_config
