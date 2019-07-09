from abc import ABC, abstractmethod
import os
import aioboto3
from utils.lambda_decorators import ssm_parameters, async_handler


class LazyInitLambda(ABC):
    def __init__(self, ssm_params_to_load):
        super(ABC, self).__init__()
        self.region = os.environ["REGION"]
        self.stage = os.environ["STAGE"]
        self.ssm_source_stage = \
            os.environ["SSM_SOURCE_STAGE"] if "SSM_SOURCE_STAGE" in os.environ else self.stage
        self.app_name = os.environ["APP_NAME"]
        self.ssm_stage_prefix = f"/{self.app_name}/{self.stage}"
        self.ssm_source_stage_prefix = f"/{self.app_name}/{self.ssm_source_stage}"
        self._ssm_params_to_load = ssm_params_to_load

        self.event = None
        self.context = None
        self.initialised = False
        self.ssm_client = None

    # Overriding this method allows subsclasses to initialise e.g. aws clients
    @abstractmethod
    def initialise(self):
        pass

    # This is how the implementor handles the event
    @abstractmethod
    async def invoke_impl(self, event, context):
        pass

    # Other ssm params can be accessed with this method, uses relative name e.g.
    # use "/lambda/layers/utils/arn", instead of "/sec-an/dev/lambda/layers/utils/arn"
    def get_ssm_param(self, full_name):
        return self.event["ssm_params"][full_name]

    def invoke(self, event, context):
        self.context = context
        self.event = event
        self.ensure_initialised()
        print(f"Loading ssm params {self._ssm_params_to_load}")

        @ssm_parameters(self.ssm_client, *self._ssm_params_to_load)
        @async_handler()
        async def handle_event_with_params(_event, _context):
            return await self.invoke_impl(event, context)

        handle_event_with_params(event, context)

    def ensure_initialised(self):
        if not self.initialised:
            self.initialised = True
            self.ssm_client = aioboto3.client("ssm", region_name=self.region)
            # call the subclasses' initialisers
            self.initialise()
