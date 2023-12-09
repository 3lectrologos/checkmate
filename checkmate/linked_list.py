import inspect


class LinkedListError(Exception):
    pass


class ListPtr:
    def __init__(self, lst, start_idx=0):
        self._lst = list(lst)
        self._idx = start_idx
        self._MAX_VAL = 99
        self._MIN_VAL = -99

    def __repr__(self):
        return repr(self._lst)

    def __eq__(self, other):
        return self._lst == other._lst

    def go_next(self):
        if self._idx < len(self._lst) - 1:
            self._idx += 1
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: Cannot \'go_next\' at the end of linked list')

    def go_prev(self):
        if self._idx > 0:
            self._idx -= 1
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: Cannot \'go_prev\' at the start of linked list')

    def has_next(self):
        return self._idx < len(self._lst) - 1

    def has_prev(self):
        return self._idx > 0

    def get_value(self):
        return self._lst[self._idx]

    def set_value(self, value):
        if isinstance(value, int) and self._MIN_VAL <= value <= self._MAX_VAL:
            self._lst[self._idx] = value
        else:
            caller_lineno = inspect.getframeinfo(inspect.stack()[1][0]).lineno
            raise LinkedListError(f'Line {caller_lineno}: List values must be integers between -99 and 99')