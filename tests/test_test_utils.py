from test_utils.test_utils import serialise_mocks, resetting_mocks
from utils.json_serialisation import dumps
import pytest
from unittest.mock import MagicMock, patch
import os


@pytest.mark.unit
def test_cant_serialise_mock_normally():
    with pytest.raises(TypeError):
        dumps(MagicMock())


@pytest.mark.unit
@serialise_mocks()
def test_can_serialise_mock_with_decorator():
    assert isinstance(dumps(MagicMock()), str)


@pytest.mark.unit
def test_fail_two_tests_without_resetting():
    shared_mock = MagicMock()

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
    shared_mock = MagicMock()

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


@pytest.mark.unit
def test_reset_despite_excpetion():
    shared_mock = MagicMock()

    @resetting_mocks(shared_mock)
    def one():
        shared_mock()
        raise Exception()

    @resetting_mocks(shared_mock)
    def two():
        shared_mock()
        shared_mock.assert_called_once()

    with pytest.raises(Exception):
        one()
    two()


@pytest.mark.unit
def test_can_combine_serialise_mocks_with_others():
    shared_mock = MagicMock()
    shared_mock.return_value = 7

    @serialise_mocks()
    @patch.dict(os.environ, {})
    @patch("aioboto3.client")
    @patch("utils.json_serialisation.stringify_all")
    def seven(aioboto_mock, stringify_mock):
        return shared_mock()

    assert seven() == 7
