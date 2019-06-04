import os
import io
import aioboto3
from utils.lambda_decorators import async_handler
from utils.tracing import create_trace_recorder
import tarfile
from collections import namedtuple
from asyncio import run, gather

region = os.environ["REGION"]
bucket = os.environ["S3_BUCKET"]
prefix = os.environ["S3_KEY_PREFIX"]
service_name = os.environ["SERVICE_NAME"]

# Enable xray tracing
#xray_recorder = create_trace_recorder(service_name)

s3_client = aioboto3.client("s3", region_name=region)


@async_handler
async def save_dead_letter(event, _):
    print(f"Dumping event {event}")
    writes = []
    for record in event["Records"]:
        msg_attrs = record['messageAttributes']
        original_req_id = msg_attrs['RequestID']
        print(f"Dumping record {record} - {original_req_id}")

        archive_bytes = _create_archive_bytes(record)

        writes.append(
            s3_client.put_object(
                Body=archive_bytes,
                Bucket=bucket,
                Key=f"{prefix}/{original_req_id}.tar.gz",
                Metadata={
                    "RequestID": original_req_id,
                    "ErrorCode": msg_attrs["ErrorCode"],
                    "ErrorMessage": msg_attrs["ErrorMessage"]
                }
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
        archive.addfile(tar_info, params_sio)
    return archive_bytes


# For developer test use only
if __name__ == "__main__":
    async def _clean_clients():
        return await gather(
            s3_client.close()
        )
    try:
        save_dead_letter({
            "Records": [
                {
                    "body": "nice",
                    "messageAttributes": {
                        "RequestID": "moo",
                        "ErrorCode": "foo",
                        "ErrorMessage": "fan"
                    }
                }
            ]},
            namedtuple("context", ["loop"])
        )
    finally:
        run(_clean_clients())
