from hashlib import sha256
from utils.json_serialisation import dumps

# Tracks context for results e.g. the main data result has key fields of scan id, address and address type
# When looking at a port the port id and protocol are pushed onto that context


class ResultsContext:
    def __init__(self, topic, non_temporal_key_fields, scan_id, start, end, task_name, sns_client):
        self.non_temporal_key = [non_temporal_key_fields]
        self.scan_id = scan_id
        self.start = start
        self.end = end
        self.topic = topic
        self.task_name = task_name
        self.sns_client = sns_client
        self.summaries = {}
        print(f"Created publication context {self.topic}, {self._key()}, {self.end}")

    def push_context(self, non_temporal_key_fields):
        self.non_temporal_key.append(non_temporal_key_fields)
        print(f"Created publication context {self.topic}, {self._key()}, {self.end}")

    def pop_context(self):
        self.non_temporal_key.pop()

    def add_summary(self, key, value):
        self.summaries[key] = value

    def add_summaries(self, summaries):
        for k, v in summaries.items():
            self.summaries[k] = v

    def _key(self):
        return "/".join(self._key_fields().values())

    def _key_fields(self):
        return {k: v for field in self.non_temporal_key for k, v in field.items()}

    def _hash_of(self, value):
        hasher = sha256()
        hasher.update(value.encode('utf-8'))
        hash_val = hasher.hexdigest()
        print(f"Mapped non-temporal key {value} to hash {hash_val}")
        return hash_val

    def post_results(self, doc_type, data, include_summaries=False):
        if include_summaries:
            for key, value in self.summaries.items():
                data[f"summary_{key}"] = value
        r = self.sns_client.publish(
            TopicArn=self.topic,
            Subject=f"{self.task_name}:{doc_type}",
            Message=dumps({
                **self._key_fields(),
                "scan_id": self.scan_id,
                "scan_start_time": self.start,
                "scan_end_time": self.end,
                **data}),
            MessageAttributes={
                "NonTemporalKey": {"StringValue": self._hash_of(self._key()), "DataType": "String"},
                "ScanEndTime": {"StringValue": self._hash_of(self.end), "DataType": "String"}
            }
        )
        print(f"Published message {r['MessageId']}")
