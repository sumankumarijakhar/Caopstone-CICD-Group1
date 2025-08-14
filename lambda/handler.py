"""Lambda entrypoint (Python)."""
from __future__ import annotations
import json
import os
import boto3
from typing import Any, Dict

from logic import route, parse_body, validate_item  # used locally; inlined at deploy

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

    r = route(path, method)

    if r == "HEALTH":
        return _response(200, {"ok": True})

    if r == "LIST":
        data = _table.scan(Limit=50)
        return _response(200, {"items": data.get("Items", [])})

    if r == "CREATE":
        body = parse_body(event.get("body"))
        ok, msg = validate_item(body)
        if not ok:
            return _response(400, {"error": msg})
        _table.put_item(Item=body)
        return _response(201, {"saved": True, "item": body})

    return _response(404, {"error": "Not found"})
