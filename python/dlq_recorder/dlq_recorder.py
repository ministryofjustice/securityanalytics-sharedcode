import os
import io
import aioboto3
import time
from utils.lambda_decorators import async_handler
import tarfile
from collections import namedtuple
from asyncio import run, gather
from aws_xray_sdk.core.lambda_launcher import LambdaContext
from aws_xray_sdk.core import xray_recorder
import pytz
from datetime import datetime

region = os.environ["REGION"]
stage = os.environ["STAGE"]
app_name = os.environ["APP_NAME"]
bucket = os.environ["S3_BUCKET"]
prefix = os.environ["S3_KEY_PREFIX"]
dlq_name = os.environ["DLQ_NAME"]

s3_client = aioboto3.client("s3", region_name=region)


@async_handler()
async def save_dead_letter(event, _):
    writes = []
    for record in event["Records"]:
        meta_data = {}
        attrs = record["attributes"]
        sent_time = attrs["SentTimestamp"]
        sent_time = datetime.fromtimestamp(
            int(sent_time) / 1000,
            pytz.utc
        ).isoformat().replace("+00:00", "Z")
        meta_data["messageId"] = msg_id = record["messageId"]
        msg_attrs = [x["StringValue"] for x in record["messageAttributes"]]
        dead_message_key = f"{prefix}/{msg_id}-{sent_time}.tar.gz"

        # updated in this order so that the attrs from the attributes beat the user supplied
        # msg attributes fields (hope the collisions never cause an issue)
        meta_data.update(msg_attrs)

        duplicate_keys = set(meta_data.keys()).intersection(set(attrs.keys()))
        if len(duplicate_keys) > 0:
            print(f"WARNING duplicate fields in both messageAttributes and attributes. Attributes' take precedence. {duplicate_keys}")
        meta_data.update(attrs)

        meta_data["DeadLetterSentTime"] = sent_time
        meta_data["DeadLetterQueueName"] = dlq_name
        meta_data["DeadLetterKey"] = dead_message_key

        archive_bytes = _create_archive_bytes(record)

        print(f"Dumping failed event {msg_id}, with metadata {meta_data}")
        writes.append(
            s3_client.put_object(
                Body=archive_bytes,
                Bucket=bucket,
                Key=dead_message_key,
                Metadata=meta_data
            )
        )
    await gather(*writes)


def _create_archive_bytes(record):
    archive_bytes = io.BytesIO()
    with tarfile.open(fileobj=archive_bytes, mode="w:gz") as archive:
        message = record["body"]
        params_sio = io.BytesIO(message.encode("utf8"))
        tar_info = tarfile.TarInfo(name="body.json")
        tar_info.size = len(message)
        params_sio.seek(0)
        archive.addfile(tar_info, params_sio)
    # to read back the bytes we just wrote, reset the index
    archive_bytes.seek(0)
    return archive_bytes


# For developer test use only
if __name__ == "__main__":
    async def _clean_clients():
        return await gather(
            s3_client.close()
        )
    try:
        xray_recorder.configure(context=LambdaContext())
        save_dead_letter({
            "Records": [
                {
                    "body": "nice",
                    "messageId": "msg1",
                    "messageAttributes": {
                        "RequestID": {
                            "stringValue": "moo",
                            "stringListValues": [],
                            "binaryListValues": [],
                            "dataType": "Number"
                        },
                        "ErrorCode": {
                            "stringValue": "foo",
                            "stringListValues": [],
                            "binaryListValues": [],
                            "dataType": "Number"
                        },
                        "ErrorMessage": {
                            "stringValue": "fan",
                            "stringListValues": [], "binaryListValues": [],
                            "dataType": "Number"
                        }
                    },
                    "attributes": {
                        "RequestID": "moo",
                        "SentTimestamp": str(int(time.time()))
                    }
                }
            ]},
            namedtuple("context", ["loop"])
        )
    finally:
        run(_clean_clients())
