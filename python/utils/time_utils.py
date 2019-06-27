import datetime
import pytz


def iso_date_string_from_timestamp(timestamp_millis):
    return datetime.datetime.fromtimestamp(int(timestamp_millis), pytz.utc).isoformat().replace('+00:00', 'Z')
