"""Common utilities for base types, functions, classes, etc."""

def _toRFC3339(dt):
    """Convert a datetime to RFC3339."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def jsonify(obj):
    """Convert an object to JSON serializable."""
    if hasattr(obj, "isoformat"):
        return _toRFC3339(obj)
    if hasattr(obj, "to_json"):
        return obj.to_json()
    print(f"WARNING: unhandled type: {type(obj)}")
    return str(obj)
