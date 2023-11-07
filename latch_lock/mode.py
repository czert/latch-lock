class Mode:
    PRESS = 0
    HOLD = 1
    LATCH = 2
    LOCK = 3

    stack = []

    def __init__(self):
        pass

    def key(self):
        return self.stack

    def press(self, key):
        # if stack is empty, stack new mode
        if not self.stack:
            self.push(key, self.PRESS)
            return self.key()

        # ignore if key is already pressed or held
        if (key, self.PRESS) in self.stack:
            return self.key()
        if (key, self.HOLD) in self.stack:
            return self.key()

        # if key is latched on top of the stack, lock it
        if self.stack[-1] == (key, self.LATCH):
            self.stack[-1] = (key, self.LOCK)
            self._latch_holds()
            return self.key()

        # if key is locked on top of the stack, fall back to second topmost lock
        if self.stack[-1] == (key, self.LOCK):
            self.stack.pop()  # remove the lock itself first
            self._fall_back()
            return self.key()

        # otherwise, stack new mode
        self.push(key, self.PRESS)
        return self.key()

    def release(self, key):
        # if stack is empty, ignore
        if not self.stack:
            return self.key()

        # if key is pressed and on top of stack, latch it
        if self.stack[-1] == (key, self.PRESS):
            self.stack[-1] = (key, self.LATCH)
            self._latch_holds()
            return self.key()

        # if key is held, fall back to its parent
        if (key, self.HOLD) in self.stack:
            pos = self._find(lambda s: s == (key, self.HOLD), 0)
            self.stack = self.stack[:pos]
            return self.key()

        # otherwise, ignore
        return self.key()

    def command(self):
        """
        Tell Mode that a command has been fired
        """
        if self._latched():
            # fall back to last lock
            self._fall_back()
        else:
            # mark presses as holds
            self._replace(self.PRESS, self.HOLD)
        return self.key()

    def push(self, key, state):
        self._replace(self.PRESS, self.HOLD)
        self.stack.append((key, state))
        return self.key()

    def pop(self):
        self.stack.pop()
        return self.key()

    def clear(self):
        self.stack = []
        return self.key()

    def _fall_back(self):
        pos = self._find(lambda m: m[1] == self.LOCK, -1)
        self.stack = self.stack[: pos + 1]

    def _latched(self):
        """
        Return True if topmost LATCH or LOCK mode is LATCH
        """
        pos = self._find(lambda m: m[1] == self.LATCH or m[1] == self.LOCK, -1)
        if pos == -1:
            return False
        return self.stack[pos][1] == self.LATCH

    def _find(self, predicate, default):
        """
        Return index of the rightmost mode in the stack that matches
        `predicate`, or `default` if there's no match
        """
        for i in range(len(self.stack)):
            if predicate(self.stack[-i - 1]):
                return len(self.stack) - i - 1
        return default

    def _latch_holds(self):
        """
        Set all held keys in the stack as latched
        """
        self._replace(self.HOLD, self.LATCH)

    def _replace(self, old, new):
        """
        Replace all occurrences of `old` states in the stack with `new`
        """
        for i, mode in enumerate(self.stack):
            if mode[1] == old:
                self.stack[i] = self.stack[i][0], new
