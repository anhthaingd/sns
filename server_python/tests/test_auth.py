from .conftest import unique_email


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_register_requires_email_and_password(client):
    r = await client.post("/api/users/register", json={"email": "", "password": ""})
    assert r.status_code == 400


async def test_register_duplicate_email(client):
    email = unique_email("dup")
    body = {"email": email, "password": "Passw0rd!", "username": "dup"}
    assert (await client.post("/api/users/register", json=body)).status_code == 201
    assert (await client.post("/api/users/register", json=body)).status_code == 409


async def test_login_wrong_password(client):
    email = unique_email("wrongpw")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})
    r = await client.post("/api/users/login", json={"email": email, "password": "nope"})
    assert r.status_code == 403


async def test_login_unknown_account(client):
    r = await client.post("/api/users/login", json={"email": unique_email("ghost"), "password": "x"})
    assert r.status_code == 404


async def test_protected_route_without_token(client):
    r = await client.get("/api/users/getByToken")
    assert r.status_code == 401


async def test_protected_route_with_bad_token(client):
    r = await client.get("/api/users/getByToken", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 403


async def test_get_by_token(client, user):
    r = await client.get("/api/users/getByToken", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == user.email
    assert body["user"]["role"]["value"] == 0
    assert body["followers"] == [] and body["following"] == []


async def test_access_token_must_not_leak_password_hash(client, user):
    """JWT payload đọc được bởi bất kỳ ai -> không được chứa hash mật khẩu."""
    import base64
    import json

    payload = user.token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    assert "password" not in claims, f"JWT lộ hash mật khẩu: {claims.keys()}"


async def test_logout_blacklists_token(client, user):
    r = await client.post("/api/users/logout", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/users/getByToken", headers=user.headers)
    assert r.status_code == 401


async def test_concurrent_register_creates_only_one_account(client, db):
    """Kiểm tra check trùng email không bị race (cần unique index ở tầng DB)."""
    import asyncio

    email = unique_email("race")
    body = {"email": email, "password": "Passw0rd!", "username": "race"}
    results = await asyncio.gather(*[client.post("/api/users/register", json=body) for _ in range(5)])

    assert sum(1 for r in results if r.status_code == 201) == 1, [r.status_code for r in results]
    assert await db.users.count_documents({"email": email}) == 1
