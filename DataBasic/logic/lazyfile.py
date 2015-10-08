import six

class LazyFile(six.Iterator):
    """
    A proxy for a File object that delays opening it until
    a read method is called.
    Currently this implements only the minimum methods to be useful,
    but it could easily be expanded.
    """
    def __init__(self, init, *args, **kwargs):
        self.init = init
        self.f = None
        self._is_lazy_opened = False

        self._lazy_args = args
        self._lazy_kwargs = kwargs

    def __getattr__(self, name):
        if not self._is_lazy_opened:
            self.f = self.init(*self._lazy_args, **self._lazy_kwargs)
            self._is_lazy_opened = True

        return getattr(self.f, name)

    def __iter__(self):
        return self

    def close(self):
        self.f.close()
        self.f = None
        self._is_lazy_opened = False

    def __next__(self):
        if not self._is_lazy_opened:
            self.f = self.init(*self._lazy_args, **self._lazy_kwargs)
            self._is_lazy_opened = True

        return next(self.f)