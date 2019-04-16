import pytest
from utils import lambda_decorators
from unittest.mock import MagicMock


@pytest.mark.unit
def test_ssm_params():
    called = False
    ssm_mock = MagicMock()
    ssm_mock.get_parameters.return_value = {
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

    @lambda_decorators.ssm_parameters(ssm_mock, "/param/name")
    def foo(event, _):
        nonlocal called
        called = True
        assert event['ssm_params'] == {
            '/sec-an/mamos/ecs/cluster': 'arn:aws:ecs:eu-west-2:447213725459:cluster/mamos-sec-an-scanning-cluster'
        }

    foo({}, None)
    assert called
