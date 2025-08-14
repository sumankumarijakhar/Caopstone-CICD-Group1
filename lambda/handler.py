"""Lambda entrypoint (Python) — S3-backed storage (items.json)."""
import json, os, time
from typing import Any, Dict, List, Optional
import boto3

# NOTE: logic.py is concatenated during synth; don't import it here.

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]
KEY = os.environ.get("BUCKET_KEY", "data/items.json")

def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(body),
    }

def _load_items() -> List[Dict[str, Any]]:
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=KEY)
        text = obj["Body"].read().decode("utf-8")
        data = json.loads(text)
        if isinstance(data, dict) and "items" in data:
            return list(data["items"])
        if isinstance(data, list):
            return list(data)
        return []
    except s3.exceptions.NoSuchKey:
        return []
    except Exception:
        return []

def _save_items(items: List[Dict[str, Any]]) -> None:
    s3.put_object(
        Bucket=BUCKET,
        Key=KEY,
        Body=json.dumps({"items": items}).encode("utf-8"),
        ContentType="application/json",
    )

def _emit_metric(op: str, ok: bool, start_ts: float) -> None:
    # CloudWatch Embedded Metric Format (simple)
    duration_ms = int((time.time() - start_ts) * 1000)
    print(json.dumps({
        "_aws": {
            "CloudWatchMetrics": [{
                "Namespace": "Capstone/App",
                "Dimensions": [["Operation"]],
                "Metrics": [
                    {"Name": "Requests", "Unit": "Count"},
                    {"Name": "Errors", "Unit": "Count"},
                    {"Name": "LatencyMs", "Unit": "Milliseconds"}
                ],
            }],
        },
        "Operation": op,
        "Requests": 1,
        "Errors": 0 if ok else 1,
        "LatencyMs": duration_ms,
    }))

def _id_from_path(path: str) -> Optional[str]:
    parts = (path or "").rstrip("/").split("/")
    return parts[-1] if len(parts) >= 3 and parts[-2] == "items" else None

def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    start = time.time()
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

    op = "UNKNOWN"
    try:
        r = route(path, method)  # type: ignore[name-defined]
        op = r

        if r == "HEALTH":
            _emit_metric(op, True, start)
            return _response(200, {"ok": True})

        if r == "STATS":
            items = _load_items()
            _emit_metric(op, True, start)
            return _response(200, {"count": len(items)})

        if r == "LIST":
            items = _load_items()
            _emit_metric(op, True, start)
            return _response(200, {"items": items})

        if r == "CREATE":
            body = parse_body(event.get("body"))  # type: ignore[name-defined]
            ok, msg = validate_item(body)         # type: ignore[name-defined]
            if not ok:
                _emit_metric(op, False, start)
                return _response(400, {"error": msg})
            items = _load_items()
            if any(it.get("id") == body["id"] for it in items):
                _emit_metric(op, False, start)
                return _response(409, {"error": "id already exists"})
            body["createdAt"] = body.get("createdAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            items.append(body)
            _save_items(items)
            _emit_metric(op, True, start)
            return _response(201, {"saved": True, "item": body})

        if r in ("GET_ONE", "UPDATE", "DELETE"):
            item_id = _id_from_path(path)
            items = _load_items()
            idx = next((i for i, it in enumerate(items) if it.get("id") == item_id), -1)
            if idx < 0:
                _emit_metric(op, False, start)
                return _response(404, {"error": "not found"})

            if r == "GET_ONE":
                _emit_metric(op, True, start)
                return _response(200, items[idx])

            if r == "UPDATE":
                body = parse_body(event.get("body"))  # type: ignore[name-defined]
                title = body.get("title")
                if not title:
                    _emit_metric(op, False, start)
                    return _response(400, {"error": "title required"})
                items[idx]["title"] = title
                items[idx]["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _save_items(items)
                _emit_metric(op, True, start)
                return _response(200, {"updated": True, "item": items[idx]})

            if r == "DELETE":
                removed = items.pop(idx)
                _save_items(items)
                _emit_metric(op, True, start)
                return _response(200, {"deleted": True, "id": removed.get("id")})

        _emit_metric(op, False, start)
        return _response(404, {"error": "Not found"})
    except Exception as e:
        _emit_metric(op, False, start)
        return _response(500, {"error": "internal", "detail": str(e)})
