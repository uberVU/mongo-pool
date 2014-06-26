"""
    Singleton metaclass.

    Usage:
        class MyClass(BaseClass):
            __metaclass__ = Singleton
"""


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class EnvironmentAwareSingleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        from core import ubvuconfig
        from mock import MagicMock

        if cls not in cls._instances:
            # Check if there is an option to explicitly
            # disable mocking.
            disable_mock = kwargs.pop('disable_mock', False)

            if (ubvuconfig.options['environment'] == 'testing'
               and not disable_mock):
                cls._instances[cls] = MagicMock()
            else:
                cls._instances[cls] = super(EnvironmentAwareSingleton, cls).__call__(*args, **kwargs)

        result = cls._instances[cls]
        if (ubvuconfig.options['environment'] == 'testing'
           and isinstance(result, MagicMock)):
            result.reset_mock()
        return result
