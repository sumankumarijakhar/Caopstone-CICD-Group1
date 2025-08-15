"""Pure helpers for routing, parsing and validation."""
from typing import Tuple, Optional, Dict, Any

def _is_item_detail(path: str) -> Optional[str]:
    # /api/items/<id>
    if not path:
        return None
    parts = path.rstrip("/").split("/")
    if len(parts) >= 3 and parts[-2] == "items":
        return parts[-1] or None
    return None

def route(path: str, method: str) -> str:
    path = (path or "").rstrip("/")
    method = (method or "GET").upper()

    # health & stats
    if path.endswith("/api/health") and method == "GET":
        return "HEALTH"
    if path.endswith("/api/stats") and method == "GET":
        return "STATS"

    # collection
    if path.endswith("/api/items") and method == "GET":
        return "LIST"
    if path.endswith("/api/items") and method == "POST":
        return "CREATE"

    # item detail
    item_id = _is_item_detail(path)
    if item_id:
        if method == "GET":
            return "GET_ONE"
        if method == "PUT":
            return "UPDATE"
        if method == "DELETE":
            return "DELETE"
    return "NOT_FOUND"

def parse_body(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        import json
        return dict(json.loads(raw))
    except Exception:
        return {}

def validate_item(item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(item, dict):
        return False, "Invalid JSON"
    if not item.get("id") or not item.get("title"):
        return False, "id and title required"
    return True, None
