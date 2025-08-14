"""Pure helpers for routing, parsing and validation."""
from __future__ import annotations
from typing import Tuple, Optional, Dict, Any

def route(path: str, method: str) -> str:
    path = (path or "").rstrip("/")
    method = (method or "GET").upper()
    if path.endswith("/api/health") and method == "GET":
        return "HEALTH"
    if path.endswith("/api/items") and method == "GET":
        return "LIST"
    if path.endswith("/api/items") and method == "POST":
        return "CREATE"
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
