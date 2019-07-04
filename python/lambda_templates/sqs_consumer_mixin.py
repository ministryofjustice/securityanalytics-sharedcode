from abc import abstractmethod, ABC
from asyncio import gather


class SqsConsumerMixin(ABC):
    def __init__(self):
        ABC.__init__(self)

    # Overriding this method allows subsclasses to initialise e.g. aws clients
    @abstractmethod
    async def initialise(self):
        pass

    @abstractmethod
    async def process_event(self, message_id, body):
        pass

    async def invoke_impl(self, event, _):
        await gather(*[
            self._invoke_scan_impl(record["messageId"], record["body"])
            for record in event["Records"]
        ])
