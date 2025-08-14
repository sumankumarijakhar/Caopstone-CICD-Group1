from lambda.logic import route, parse_body, validate_item

def test_route_health():
    assert route("/api/health", "GET") == "HEALTH"

def test_route_list():
    assert route("/api/items", "GET") == "LIST"

def test_route_create():
    assert route("/api/items", "POST") == "CREATE"

def test_route_not_found():
    assert route("/x", "GET") == "NOT_FOUND"

def test_parse_body_valid():
    assert parse_body('{"a":1}') == {"a": 1}

def test_parse_body_invalid():
    assert parse_body("{oops}") == {}

def test_validate_item():
    assert validate_item({"id":"1","title":"t"}) == (True, None)
    assert validate_item({}) == (False, "id and title required")
