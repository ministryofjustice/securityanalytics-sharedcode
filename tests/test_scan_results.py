import pytest
from unittest.mock import MagicMock
from utils.scan_results import ResultsContext
from utils.time_utils import iso_date_string_from_timestamp
from utils.json_serialisation import dumps


@pytest.mark.unit
def test_publish_no_data():
    mock_sns_client = MagicMock()
    mock_sns_client.publish.return_value = {"MessageId": "Msg32"}
    context = ResultsContext("PubTopic", {"address": "123.123.123.123"}, "scan_12",
                             iso_date_string_from_timestamp(123456), iso_date_string_from_timestamp(789123),
                             "scan_name", mock_sns_client)

    context.publish_results()

    # it should publish the top level info parent and temporal key
    mock_sns_client.publish.assert_called_with(
        TopicArn="PubTopic",
        Subject="scan_name",
        Message=dumps(
            {
                "scan_id": "scan_12",
                "scan_start_time": iso_date_string_from_timestamp(123456),
                "scan_end_time": iso_date_string_from_timestamp(789123),
                "__docs": {}
            }
        ),
        MessageAttributes={
            "ParentKey": {"StringValue": ResultsContext._hash_of("123.123.123.123"), "DataType": "String"},
            "TemporalKey": {"StringValue": ResultsContext._hash_of(iso_date_string_from_timestamp(789123)),
                            "DataType": "String"}
        }
    )


@pytest.mark.unit
def test_context_push_and_pop():
    mock_sns_client = MagicMock()
    mock_sns_client.publish.return_value = {"MessageId": "Msg32"}
    context = ResultsContext("PubTopic", {"address": "123.456.123.456"}, "scan_2", iso_date_string_from_timestamp(4),
                             iso_date_string_from_timestamp(5), "scan_name", mock_sns_client)

    context.push_context({"port": "22"})
    context.post_results("port_info", {"open": "false"})
    context.push_context({"vulnerability": "cve4"})
    context.post_results("vuln_info", {"severity": "5"})
    context.pop_context()
    context.push_context({"vulnerability": "cve5"})
    context.post_results("vuln_info", {"severity": "2"})
    context.pop_context()
    context.pop_context()
    context.push_context({"port": "80"})
    context.post_results("port_info", {"open": "true"})
    context.pop_context()
    context.post_results("host_info", {"uptime": "1234567"})
    context.publish_results()

    # it should publish the top level info parent and temporal key
    mock_sns_client.publish.assert_called_with(
        TopicArn="PubTopic",
        Subject="scan_name",
        Message=dumps(
            {
                "scan_id": "scan_2",
                "scan_start_time": iso_date_string_from_timestamp(4),
                "scan_end_time": iso_date_string_from_timestamp(5),
                "__docs": {
                    "port_info": [
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                                "port": "22"
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "port": "22",
                                "open": "false",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        },
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                                "port": "80"
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "port": "80",
                                "open": "true",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        }
                    ],
                    "vuln_info": [
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                                "port": "22",
                                "vulnerability": "cve4"
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "port": "22",
                                "vulnerability": "cve4",
                                "severity": "5",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        },
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                                "port": "22",
                                "vulnerability": "cve5"
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "port": "22",
                                "vulnerability": "cve5",
                                "severity": "2",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        }
                    ],
                    "host_info": [
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "uptime": "1234567",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        }
                    ]
                }
            }
        ),
        MessageAttributes={
            "ParentKey": {
                "StringValue": ResultsContext._hash_of({"address": "123.456.123.456"}),
                "DataType": "String"
            },
            "TemporalKey": {
                "StringValue": ResultsContext._hash_of(iso_date_string_from_timestamp(5)),
                "DataType": "String"
            }
        }
    )


@pytest.mark.unit
def test_summary_info_published():
    mock_sns_client = MagicMock()
    mock_sns_client.publish.return_value = {"MessageId": "Msg32"}
    context = ResultsContext("PubTopic", {"address": "123.456.123.456"}, "scan_9", iso_date_string_from_timestamp(4),
                             iso_date_string_from_timestamp(5), "scan_name", mock_sns_client)

    context.add_summaries({"foo": "bar", "boo": "baz"})
    context.add_summary("banana", "man")
    context.post_results("host_info", {"uptime": "1234567"}, include_summaries=True)
    context.publish_results()

    mock_sns_client.publish.assert_called_with(
        TopicArn="PubTopic",
        Subject="scan_name",
        Message=dumps(
            {
                "scan_id": "scan_9",
                "scan_start_time": iso_date_string_from_timestamp(4),
                "scan_end_time": iso_date_string_from_timestamp(5),
                "__docs": {
                    "host_info": [
                        {
                            "NonTemporalKey": ResultsContext._hash_of({
                                "address": "123.456.123.456",
                            }),
                            "Data": {
                                "address": "123.456.123.456",
                                "uptime": "1234567",
                                "summary_foo": "bar",
                                "summary_boo": "baz",
                                "summary_banana": "man",
                                "__ParentKey": ResultsContext._hash_of({"address": "123.456.123.456"}),
                            }
                        }
                    ]
                }
            }
        ),
        MessageAttributes={
            "ParentKey": {
                "StringValue": ResultsContext._hash_of({"address": "123.456.123.456"}),
                "DataType": "String"
            },
            "TemporalKey": {
                "StringValue": ResultsContext._hash_of(iso_date_string_from_timestamp(5)),
                "DataType": "String"
            }
        }
    )
