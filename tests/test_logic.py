from lambda.logic import route, parse_body, validate_item

def test_route_health():  assert route("/api/health", "GET") == "HEALTH"
def test_route_list():    assert route("/api/items", "GET") == "LIST"
def test_route_create():  assert route("/api/items", "POST") == "CREATE"
def test_route_get_one(): assert route("/api/items/123", "GET") == "GET_ONE"
def test_route_update():  assert route("/api/items/123", "PUT") == "UPDATE"
def test_route_delete():  assert route("/api/items/abc", "DELETE") == "DELETE"
def test_route_stats():   assert route("/api/stats", "GET") == "STATS"

def test_parse_body_valid():   assert parse_body('{"a":1}') == {"a": 1}
def test_parse_body_invalid(): assert parse_body("{oops}") == {}
def test_validate_item():      assert validate_item({"id":"1","title":"t"}) == (True, None)
