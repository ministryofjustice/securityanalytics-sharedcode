from functools import wraps
from utils import json_serialisation
from asyncio import Future
from unittest.mock import MagicMock


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


# Magic mock deliberately stops you mocking magic methods e.g. __str__ and __aexit
# Its ok because it mocks most things already, but not aexit and aenter.
# This little wrapper is inspired by
# http://pfertyk.me/2017/06/testing-asynchronous-context-managers-in-python/
class AsyncContextManagerMock(MagicMock):
    async def __aenter__(self):
        return self.aenter

    async def __aexit__(self, *args):
        pass


def coroutine_of(value):
    async def coro():
        return value
    return coro()


def future_of(value):
    future = Future()
    future.set_result(value)
    return future


def future_exception(exception):
    future = Future()
    future.set_exception(exception)
    return future
