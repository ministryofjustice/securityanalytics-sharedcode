from functools import wraps
from utils import json_serialisation
from asyncio import Future


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


def future_of(value):
    future = Future()
    future.set_result(value)
    return future


def future_exception(exception):
    future = Future()
    future.set_exception(exception)
    return future
