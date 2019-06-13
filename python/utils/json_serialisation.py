from datetime import date, datetime
from decimal import Decimal
import json

# Icky global used when testing to allow the serialisation of mocks
stringify_all = False


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, set):
        return "{}" if len(obj) == 0 else str(obj)
    elif stringify_all:
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))


def dumps(obj, **kwargs):
    return json.dumps(obj, default=json_serial, **kwargs)
