class DelayedCallable():
    def __init__(self, func, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.func = func
        self._value = None
    
    @property
    def value(self):
        if self._value is None:
            self._value = self.func(*self.args, **self.kwargs)
        return self._value
