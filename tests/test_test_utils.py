from test_utils.test_utils import serialise_mocks, resetting_mocks
from utils.json_serialisation import dumps
import pytest
from unittest import mock


@pytest.mark.unit
def test_cant_serialise_mock_normally():
    with pytest.raises(TypeError):
        dumps(mock.MagicMock())


@pytest.mark.unit
@serialise_mocks()
def test_can_serialise_mock_with_decorator():
    assert isinstance(dumps(mock.MagicMock()), str)




@pytest.mark.unit
def test_fail_two_tests_without_resetting():
    shared_mock = mock.MagicMock()

    def one():
        shared_mock()
        shared_mock.assert_called_once()

    def two():
        shared_mock()
        shared_mock.assert_called_once()

    with pytest.raises(AssertionError):
        one()
        two()


@pytest.mark.unit
def test_pass_two_tests_with_resetting():
    shared_mock = mock.MagicMock()

    @resetting_mocks(shared_mock)
    def one():
        shared_mock()
        shared_mock.assert_called_once()

    @resetting_mocks(shared_mock)
    def two():
        shared_mock()
        shared_mock.assert_called_once()

    one()
    two()
