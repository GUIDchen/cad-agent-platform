def test_csrf_required_for_cookie_requests(client):
    client.cookies.clear()
    assert client.post("/api/auth/dev-login", json={"name": "designer"}).status_code == 200
    token = client.cookies.get("csrf_token")
    assert token

    assert client.post("/api/projects", json={"name": "csrf-a"}).status_code == 403
    ok = client.post("/api/projects", json={"name": "csrf-b"}, headers={"X-CSRF-Token": token})
    assert ok.status_code == 201
