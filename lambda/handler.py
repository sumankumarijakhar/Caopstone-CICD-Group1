"""Lambda entrypoint (Python) — S3-backed storage (items.json)."""
import json
import os
import boto3
from typing import Any, Dict

# helpers (from logic.py) are concatenated during CDK synth; do NOT import logic here.

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]
KEY = os.environ.get("BUCKET_KEY", "data/items.json")

def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}

def _load_items() -> list[dict]:
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=KEY)
        text = obj["Body"].read().decode("utf-8")
        data = json.loads(text)
        return data["items"] if isinstance(data, dict) and "items" in data else (data if isinstance(data, list) else [])
    except s3.exceptions.NoSuchKey:
        return []
    except Exception:
        # keep it resilient for the demo
        return []

def _save_items(items: list[dict]) -> None:
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=json.dumps(items).encode("utf-8"), ContentType="application/json")

def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    # Support Lambda URL and API Gateway-like events
    path = event.get("path") or event.get("rawPath") or event.get("requestContext", {}).get("http", {}).get("path") or ""
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "GET"

    # Provided by inlined logic.py
    r = route(path, method)  # type: ignore[name-defined]

    if r == "HEALTH":
        return _response(200, {"ok": True})

    if r == "LIST":
        return _response(200, {"items": _load_items()})

    if r == "CREATE":
        body_raw = event.get("body")
        body = parse_body(body_raw)  # type: ignore[name-defined]
        ok, msg = validate_item(body)  # type: ignore[name-defined]
        if not ok:
            return _response(400, {"error": msg})
        items = _load_items()
        items.append(body)
        _save_items(items)
        return _response(201, {"saved": True, "item": body})

    return _response(404, {"error": "Not found"})
