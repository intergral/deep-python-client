FIRE_COUNT = "fire_count"
WINDOW_START = "window_start"
WINDOW_END = "window_end"
CONDITION = "condition"

"""This is the key to indicate the frame collection type"""
FRAME_TYPE = 'frame_type'
"""This is the key to indicate the stack collection type"""
STACK_TYPE = 'stack_type'

"""Collect only the frame we are on"""
SINGLE_FRAME_TYPE = 'single_frame'
"""Collect from all available frames"""
ALL_FRAME_TYPE = 'all_frame'
"""Collect on frame data"""
NO_FRAME_TYPE = 'no_frame'

"""Collect the full stack"""
STACK = 'stack'
"""Do not collect the stack data"""
NO_STACK = 'no_stack'


def frame_type_ordinal(frame_type):
    if frame_type == SINGLE_FRAME_TYPE:
        return 1
    if frame_type == ALL_FRAME_TYPE:
        return 2
    if frame_type == NO_FRAME_TYPE:
        return 0


class TracepointWindow:
    def __init__(self, start, end):
        self._start = start
        self._end = end

    def in_window(self, ts):
        if self._start == 0 and self._end == 0:
            return True
        return self._start <= ts <= self._end


class TracePointConfig:
    def __init__(self, tp_id: str, path: str, line_no: int, args: dict, watches: list):
        self._id = tp_id
        self._path = path
        self._line_no = line_no
        self._args = args
        self._watches = watches
        self._window = TracepointWindow(self.get_arg(WINDOW_START, 0), self.get_arg(WINDOW_END, 0))
        self._stats = TracepointExecutionStats()

    @property
    def id(self):
        return self._id

    @property
    def path(self):
        return self._path

    @property
    def line_no(self):
        return self._line_no

    @property
    def args(self):
        return self._args

    @property
    def watches(self):
        return self._watches

    @property
    def frame_type(self):
        return self.get_arg(FRAME_TYPE, SINGLE_FRAME_TYPE)

    @property
    def stack_type(self):
        return self.get_arg(STACK_TYPE, STACK)

    @property
    def fire_count(self):
        """
        Get the allowed number of triggers

        :return: the configured number of triggers, or -1 for unlimited triggers
        """
        return self.get_arg_int(FIRE_COUNT, -1)

    @property
    def condition(self):
        return self.get_arg(CONDITION, None)

    def get_arg(self, name, default_value):
        if name in self._args:
            return self._args[name]
        return default_value

    def get_arg_int(self, name, default_value):
        return int(self.get_arg(name, default_value))

    def can_trigger(self, ts):
        """
        Check if the tracepoint can trigger, this is to check the config. e.g. fire count, fire windows etc
        :param ts: the time the tracepoint has been triggered
        :return: true, if we should collect data; else false
        """
        if self.fire_count <= self._stats.fire_count:
            return False
        if not self._window.in_window(ts):
            return False
        return True

    def has_triggered(self, ts):
        """This is called when the tracepoint has been processed."""
        self._stats.fire(ts)

    def __str__(self) -> str:
        return str({'id': self._id, 'path': self._path, 'line_no': self._line_no, 'args': self._args,
                    'watches': self._watches})

    def __repr__(self) -> str:
        return self.__str__()

    def collect_trace(self):
        pass

    def collect_variables(self):
        pass


class TracepointExecutionStats:
    def __init__(self):
        self._fire_count = 0
        self._last_fire = 0

    def fire(self, ts):
        self._fire_count += 1
        self._last_fire = ts

    @property
    def fire_count(self):
        return self._fire_count

    @property
    def last_fire(self):
        return self._last_fire
