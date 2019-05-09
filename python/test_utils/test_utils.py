from functools import wraps
from utils import json_serialisation


def resetting_mocks(*mocks):
    def decorator(handler):
        @wraps(handler)
        def wrapper():
            try:
                handler()
            finally:
                for mock in mocks:
                    mock.reset_mock(return_value=True, side_effect=True)
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
