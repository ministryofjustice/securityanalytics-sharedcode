from functools import wraps
from utils import json_serialisation


def resetting_mocks(*mocks):
    def decorator(handler):
        @wraps(handler)
        def wrapper():
            handler()
            for mock in mocks:
                mock.reset_mock()
        return wrapper
    return decorator


def serialise_mocks():
    def decorator(handler):
        @wraps(handler)
        def wrapper():
            old_val = json_serialisation.stringify_all
            json_serialisation.stringify_all = True
            handler()
            json_serialisation.stringify_all = old_val
        return wrapper
    return decorator
