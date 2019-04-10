from datetime import date, datetime
import json


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def dumps(obj, **kwargs):
    return json.dumps(obj, default=json_serial, **kwargs)
