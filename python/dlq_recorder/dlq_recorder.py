import os
import io
import aioboto3
import time
from utils.json_serialisation import dumps
from utils.lambda_decorators import async_handler, ssm_parameters
import tarfile
from collections import namedtuple
from asyncio import run, gather
from aws_xray_sdk.core.lambda_launcher import LambdaContext
from aws_xray_sdk.core import xray_recorder

region = os.environ["REGION"]
stage = os.environ["STAGE"]
app_name = os.environ["APP_NAME"]
bucket = os.environ["S3_BUCKET"]
prefix = os.environ["S3_KEY_PREFIX"]
dlq_name = os.environ["DLQ_NAME"]

ssm_client = aioboto3.client("ssm", region_name=region)
s3_client = aioboto3.client("s3", region_name=region)
sqs_client = aioboto3.client("sqs", region_name=region)


ssm_prefix = f"/{app_name}/{stage}"
ES_SQS = f"{ssm_prefix}/analytics/elastic/ingest_queue/id"


@ssm_parameters(
    ssm_client,
    ES_SQS
)
@async_handler(xray=True)
async def save_dead_letter(event, _):
    es_queue = event['ssm_params'][ES_SQS]
    writes = []
    for record in event["Records"]:
        meta_data = {}
        attrs = record["attributes"]
        sent_time = attrs["SentTimestamp"]
        msg_id = record["messageId"]
        msg_attrs = record["messageAttributes"]

        # updated in this order so that the attrs from the attributes beat the user supplied
        # msg attributes fields (hope the collisions never cause an issue)
        meta_data.update(msg_attrs)

        duplicate_keys = set(meta_data.keys()).intersection(set(attrs.keys()))
        if len(duplicate_keys) > 0:
            print(f"WARNING duplicate fields in both messageAttributes and attributes. Attributes' take precedence. {duplicate_keys}")
        meta_data.update(attrs)

        archive_bytes = _create_archive_bytes(record)
        dead_message_key = f"{prefix}/{msg_id}-{sent_time}.tar.gz"

        elastic_stats = {}
        elastic_stats.update(meta_data)
        elastic_stats["DeadMessageBucket"] = bucket
        elastic_stats["DeadMessageKey"] = dead_message_key
        elastic_key = {
            "NonTemporalKey": msg_id,
            # TODO rename scan end time in elastic ingestor to more general name
            "ScanEndTime": sent_time
        }

        print(f"Dumping failed event {msg_id}")

        writes += [
            s3_client.put_object(
                Body=archive_bytes,
                Bucket=bucket,
                Key=dead_message_key,
                Metadata=meta_data
            ),
            sqs_client.send_message(
                QueueUrl=es_queue,
                Subject=f"dead_letters:{dlq_name}",
                MessageBody=dumps(elastic_stats),
                MessageAttributes=elastic_key
            )
        ]
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
                        "RequestID": "moo",
                        "ErrorCode": "foo",
                        "ErrorMessage": "fan"
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
