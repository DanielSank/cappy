class Future:
    def __init__(self):
        self.callbacks = []
        self._fired = False
        self.result = None

    def add_callback(self, callback):
        self.callbacks.append(callback)
        if self._fired:
            self._execute_callbacks(self.result)

    def fire(self, result=None):
        if self._fired == True:
            raise RuntimeError("Cannot fire Future twice")
        self._fired = True
        self._execute_callbacks(result)

    def _execute_callbacks(self, result):
        self.result = result
        while len(self.callbacks):
            cb = self.callbacks.pop(0)
            self.result = cb(self.result)
            if isinstance(self.result, Future):
                self.result.add_callback(self._execute_callbacks)
                break


def call_as_future(func, *args):
    result = func(*args)
    if isinstance(result, Future):
        return result
    else:
        f = Future()
        f.fire(result)
        return f

