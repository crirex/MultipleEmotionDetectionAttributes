# class Singleton(object):
#     _instances = {}
#
#     def __call__(self, *args, **kwargs):
#         if self not in self._instances:
#             self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)
#         return self._instances[self]


class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
