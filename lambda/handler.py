"""Lambda entrypoint (Python)."""
import json
import os
import boto3
from typing import Any, Dict

# NOTE: do NOT import from logic at runtime; we inline it during deploy.
# from logic import route, parse_body, validate_item

# --- inlined helpers start (CDK concatenates logic.py above this file) ---

# --- inlined helpers end ---

_ddb = boto3.resource("dynamodb")
_table = _ddb.Table(os.environ["TABLE_NAME"])

def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }

def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    path = (
        event.get("path")
        or event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or ""
    )
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or "GET"
    )

    # route/parse_body/validate_item are provided by the inlined logic.py
    r = route(path, method)  # type: ignore[name-defined]

    if r == "HEALTH":
        return _response(200, {"ok": True})

    if r == "LIST":
        data = _table.scan(Limit=50)
        return _response(200, {"items": data.get("Items", [])})

    if r == "CREATE":
        body = parse_body(event.get("body"))  # type: ignore[name-defined]
        ok, msg = validate_item(body)         # type: ignore[name-defined]
        if not ok:
            return _response(400, {"error": msg})
        _table.put_item(Item=body)
        return _response(201, {"saved": True, "item": body})

    return _response(404, {"error": "Not found"})
