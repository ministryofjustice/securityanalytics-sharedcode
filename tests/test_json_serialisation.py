import pytest
from datetime import date, datetime
from utils import json_serialisation


@pytest.mark.unit
def test_serialisation():
    object_to_serialise = {'date': date.fromtimestamp(1234567), 'datetime': datetime.utcfromtimestamp(1234567)}
    assert json_serialisation.dumps(object_to_serialise) == \
        "{\"date\": \"1970-01-15\", \"datetime\": \"1970-01-15T06:56:07\"}"
