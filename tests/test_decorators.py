import pytest
import os
from utils import lambda_decorators
from unittest.mock import MagicMock, patch
from asyncio import get_running_loop
from lambda_templates.lazy_initialising_lambda import LazyInitLambda
from test_utils.test_utils import coroutine_of


@pytest.mark.unit
def test_ssm_params():
    called = False
    ssm_mock = MagicMock()

    async def get_parameters():
        return {
            "Parameters":
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
        assert event["ssm_params"] == {
            "/sec-an/mamos/ecs/cluster": "arn:aws:ecs:eu-west-2:447213725459:cluster/mamos-sec-an-scanning-cluster"
        }

    foo({}, None)
    assert called


@pytest.mark.unit
def test_suppress_exceptions_throw_exceptional_return():
    @lambda_decorators.suppress_exceptions(Exception("Rethrow"))
    def foo(event, _):
        raise Exception("Original")

    with pytest.raises(Exception, match="Rethrow"):
        foo({}, None)


@pytest.mark.unit
def test_suppress_exceptions_return_value():
    @lambda_decorators.suppress_exceptions(5)
    def foo(event, _):
        raise Exception("Original")

    assert foo({}, None) == 5


@pytest.mark.unit
def test_async_decorator():
    @patch.dict(os.environ, {"USE_XRAY": "0"})
    @lambda_decorators.async_handler()
    async def foo(event, _):
        assert get_running_loop()

    foo({}, MagicMock())


@pytest.mark.unit
def test_async_decorator_on_class():
    hit = False

    class Foo:
        @patch.dict(os.environ, {"USE_XRAY": "0"})
        @lambda_decorators.async_handler()
        async def foo(self, event, _):
            nonlocal hit
            hit = True
            assert get_running_loop()

    Foo().foo({}, MagicMock())
    assert hit


TEST_ENV = {
    "REGION": "region",
    "STAGE": "dev",
    "APP_NAME": "moo"
}
@pytest.mark.unit
@patch.dict(os.environ, TEST_ENV)
@patch("aioboto3.client")
def test_async_decorator_on_lazy(client_mock):
    hit = False

    mock_sqs_client = MagicMock()
    client_mock.return_value = mock_sqs_client

    mock_sqs_client.get_parameters.return_value = coroutine_of({"Parameters": []})

    class Foo(LazyInitLambda):
        def __init__(self):
            LazyInitLambda.__init__(self)

        def ssm_parameters_to_load(self):
            return []

        async def invoke_impl(self, event, context):
            nonlocal hit
            hit = True
            assert get_running_loop()

        def initialise(self):
            pass

    Foo().invoke({}, MagicMock())
    assert hit
