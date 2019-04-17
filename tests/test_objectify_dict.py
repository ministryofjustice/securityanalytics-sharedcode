from utils.objectify_dict import objectify
import pytest


@pytest.mark.unit
def test_objectification_of_dict():
    test_input = {'foo': {'bar': {'baz': 3}}, 'bar': [{'baz': 'a'}, {'baz': 'b'}]}
    result = objectify(test_input)

    assert result.foo.bar.baz == 3
    assert result.bar[0].baz == 'a'
    assert result.bar[1].baz == 'b'


@pytest.mark.unit
def test_objectification_of_list():
    test_input = [{'baz': 'a'}, {'baz': 'b'}]
    result = objectify(test_input)

    assert result[0].baz == 'a'
    assert result[1].baz == 'b'


@pytest.mark.unit
def test_objectification_of_tuple():
    test_input = ({'baz': 'a'}, {'baz': 'b'})
    result = objectify(test_input)

    assert result[0].baz == 'a'
    assert result[1].baz == 'b'

