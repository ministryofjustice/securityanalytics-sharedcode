import pytest
from utils import lambda_decorators
from unittest.mock import MagicMock


@pytest.mark.unit
def test_ssm_params():
    called = False
    ssm_mock = MagicMock()

    async def get_parameters():
        return {
            'Parameters':
            [
                {
                    "Name": "/sec-an/mamos/ecs/cluster",
                    "Type": "StringList",
                    "Value": "arn:aws:ecs:eu-west-2:447213725459:cluster/mamos-sec-an-scanning-cluster",
                    "Version": 1,
                    "LastModifiedDate": "2019-04-08T13:01:12.317000+00:00",
                    "ARN": "arn:aws:ssm:eu-west-2:447213725459:parameter/sec-an/mamos/ecs/cluster"}
            ]
        }
    ssm_mock.get_parameters.return_value = get_parameters()

    @lambda_decorators.ssm_parameters(ssm_mock, "/param/name")
    def foo(event, _):
        nonlocal called
        called = True
        assert event['ssm_params'] == {
            '/sec-an/mamos/ecs/cluster': 'arn:aws:ecs:eu-west-2:447213725459:cluster/mamos-sec-an-scanning-cluster'
        }

    foo({}, None)
    assert called


@pytest.mark.unit
def test_suppress_exceptions_throw_exceptional_return():
    @lambda_decorators.suppress_exceptions(Exception('Rethrow'))
    def foo(event, _):
        raise Exception('Original')

    with pytest.raises(Exception, match="Rethrow"):
        foo({}, None)


@pytest.mark.unit
def test_suppress_exceptions_return_value():
    @lambda_decorators.suppress_exceptions(5)
    def foo(event, _):
        raise Exception('Original')

    assert foo({}, None) == 5
