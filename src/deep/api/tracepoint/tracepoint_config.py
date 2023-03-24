class TracePointConfig:
    def __init__(self, tp_id: str, path: str, line_no: int, args: dict, watches: list):
        self._id = tp_id
        self._path = path
        self._line_no = line_no
        self._args = args
        self._watches = watches

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

    def __str__(self) -> str:
        return str({'id': self._id, 'path': self._path, 'line_no': self._line_no, 'args': self._args,
                    'watches': self._watches})

    def __repr__(self) -> str:
        return self.__str__()
