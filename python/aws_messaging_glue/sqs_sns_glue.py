import os
import aioboto3
from utils.lambda_decorators import async_handler
from asyncio import gather, run
from collections import namedtuple

region = os.environ["REGION"]
stage = os.environ["STAGE"]
app_name = os.environ["APP_NAME"]

topic = os.environ["TOPIC"]

ssm_client = aioboto3.client("ssm", region_name=region)
sns_client = aioboto3.client("sns", region_name=region)


@async_handler
async def forward_messages(event, _):
    coros = []
    for record in event["Records"]:
        msg_id = record["messageId"]
        print(f"Forwarding message {msg_id}")
        body = record["body"]
        msg_attributes = record["messageAttributes"]

        coros.append(sns_client.publish(
            TopicArn=topic,
            Subject=msg_id,
            Message=body,
            MessageAttributes=msg_attributes
        ))
    await gather(*coros)

# For developer test use only
if __name__ == "__main__":
    async def _clean_clients():
        return await gather(
            ssm_client.close(),
            sns_client.close()
        )
    try:
        forward_messages({}, namedtuple("context", ["loop"]))
    finally:
        run(_clean_clients())
