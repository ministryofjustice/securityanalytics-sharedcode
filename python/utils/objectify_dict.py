from collections import namedtuple


# This method will recursively convert dictionaries into named tuples, allowing them to be
# used like they were regular objects e.g. foo.bar.baz not foo['bar']['baz']
# it does trade readability of code for a performance hit doing the conversion
def objectify(v):
    if isinstance(v, dict):
        for key, value in v.items():
            if isinstance(value, (dict, list, tuple)):
                v[key] = objectify(value)
        return namedtuple('t', v.keys())(**v)
    if isinstance(v, list):
        return [objectify(x) for x in v]
    if isinstance(v, tuple):
        return tuple(objectify(x) for x in v)
    else:
        return v

