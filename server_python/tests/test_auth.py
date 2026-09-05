import base64
import json

import pytest

from .conftest import unique_email


def _decode_claims(token: str) -> dict:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200


async def test_register_rejects_malformed_email(client):
    """Email rỗng/sai định dạng bị chặn ngay ở tầng schema."""
    r = await client.post("/api/users/register", json={"email": "", "password": ""})
    assert r.status_code == 422, r.text
    assert r.json()["message"], "response 422 phải có `message` cho toast của client"


async def test_register_requires_password(client):
    r = await client.post("/api/users/register", json={"email": unique_email("nopw")})
    assert r.status_code == 400, r.text
    assert r.json()["message"] == "Yêu cầu cần có email và password!"


async def test_register_duplicate_email(client):
    email = unique_email("dup")
    body = {"email": email, "password": "Passw0rd!", "username": "dup"}
    assert (await client.post("/api/users/register", json=body)).status_code == 201
    assert (await client.post("/api/users/register", json=body)).status_code == 409


async def test_login_failure_does_not_reveal_whether_email_exists(client):
    """Sai mật khẩu và email không tồn tại phải trả CÙNG status + CÙNG thông báo.

    Bản cũ trả 404 "Tài khoản chưa được đăng ký!" cho email lạ và 403
    "Sai mật khẩu!" cho email có thật -> chỉ cần thử một lần là biết email nào
    đã đăng ký trong hệ thống.
    """
    email = unique_email("wrongpw")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})

    wrong_password = await client.post("/api/users/login", json={"email": email, "password": "nope"})
    unknown_email = await client.post("/api/users/login", json={"email": unique_email("ghost"), "password": "x"})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["message"] == unknown_email.json()["message"]


async def test_login_rejects_wrong_types_with_422(client):
    """`{"email": 123, "password": []}` trước đây đi thẳng xuống truy vấn Mongo."""
    r = await client.post("/api/users/login", json={"email": 123, "password": []})
    assert r.status_code == 422, r.text
    assert r.json()["message"]


async def test_login_is_rate_limited_per_email(client):
    """Dò mật khẩu một tài khoản bị chặn sau ngưỡng lần thất bại."""
    email = unique_email("bruteforce")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})

    statuses = []
    for _ in range(12):
        r = await client.post("/api/users/login", json={"email": email, "password": "sai-mat-khau"})
        statuses.append(r.status_code)

    assert 429 in statuses, f"không bao giờ bị chặn: {statuses}"
    # Đúng mật khẩu cũng không qua được khi đã bị khoá -> khoá thật sự có hiệu lực.
    r = await client.post("/api/users/login", json={"email": email, "password": "Passw0rd!"})
    assert r.status_code == 429, r.text


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
    claims = _decode_claims(user.token)
    assert "password" not in claims, f"JWT lộ hash mật khẩu: {claims.keys()}"


async def test_logout_blacklists_token(client, user):
    r = await client.post("/api/users/logout", headers=user.headers)
    assert r.status_code == 200
    r = await client.get("/api/users/getByToken", headers=user.headers)
    assert r.status_code == 401


async def test_access_token_carries_only_needed_claims(client, user):
    """Token đi kèm MỌI request -> không nhét dữ liệu hồ sơ vào đó."""
    claims = _decode_claims(user.token)
    assert set(claims) <= {"_id", "email", "username", "role", "type", "jti", "iat", "exp"}, claims.keys()


async def test_login_sets_httponly_refresh_cookie(client):
    email = unique_email("cookie")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})
    r = await client.post("/api/users/login", json={"email": email, "password": "Passw0rd!"})
    assert r.status_code == 200, r.text

    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie, set_cookie
    assert "HttpOnly" in set_cookie, "refresh token phải httpOnly, nếu không XSS lấy được"


async def test_refresh_issues_new_access_token_and_rotates(client):
    email = unique_email("refresh")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})
    login = await client.post("/api/users/login", json={"email": email, "password": "Passw0rd!"})
    old_cookie = client.cookies.get("refresh_token")
    assert old_cookie

    r = await client.post("/api/users/refresh")
    assert r.status_code == 200, r.text
    new_token = r.json()["accessToken"]
    assert new_token != login.json()["accessToken"]

    # Token mới dùng được ngay.
    me = await client.get("/api/users/getByToken", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200, me.text

    # Xoay vòng: refresh token cũ bị thu hồi, dùng lại không được.
    # Dùng client riêng vì `client` đã thay cookie bằng token mới.
    import httpx

    from .conftest import BASE_URL

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as replay_client:
        replay_client.cookies.set("refresh_token", old_cookie)
        replay = await replay_client.post("/api/users/refresh")
    assert replay.status_code == 401, replay.text


async def test_refresh_token_cannot_be_used_as_access_token(client):
    """REFRESH_TOKEN_SECRET có thể trùng ACCESS_TOKEN_SECRET -> phải chặn bằng claim `type`."""
    email = unique_email("mixup")
    await client.post("/api/users/register", json={"email": email, "password": "Passw0rd!"})
    await client.post("/api/users/login", json={"email": email, "password": "Passw0rd!"})
    refresh_token = client.cookies.get("refresh_token")

    r = await client.get("/api/users/getByToken", headers={"Authorization": f"Bearer {refresh_token}"})
    assert r.status_code == 403, r.text


async def test_invalid_object_id_does_not_leak_driver_message(client):
    """Thông báo lỗi của bson mô tả cấu trúc nội bộ -> không được ra tới client."""
    r = await client.get("/api/users/khong-phai-objectid")
    assert r.status_code == 400, r.text
    message = r.json()["message"]
    assert "ObjectId" not in message and "12-byte" not in message, message


async def test_concurrent_register_creates_only_one_account(client, db):
    """Kiểm tra check trùng email không bị race (cần unique index ở tầng DB)."""
    import asyncio

    email = unique_email("race")
    body = {"email": email, "password": "Passw0rd!", "username": "race"}
    results = await asyncio.gather(*[client.post("/api/users/register", json=body) for _ in range(5)])

    assert sum(1 for r in results if r.status_code == 201) == 1, [r.status_code for r in results]
    assert await db.users.count_documents({"email": email}) == 1


async def test_revoked_token_is_stored_in_shared_state_not_process_memory(client, user):
    """Đăng xuất phải ghi vào Redis, không phải `set()` trong RAM tiến trình.

    Đây là test hồi quy cho lỗ đã kiểm chứng được ở bản cũ:

        POST /api/users/logout          -> OK
        GET  /api/users/getByToken      -> 401   (đã chặn)
        docker compose restart server
        GET  /api/users/getByToken      -> 200   (token sống lại!)

    Không restart được backend từ trong bộ test, nên kiểm đúng cái tính chất
    khiến nó sống sót: bản ghi thu hồi nằm ở kho dùng chung, tồn tại độc lập với
    tiến trình backend, và có TTL để Redis tự dọn.
    """
    import os

    from redis.asyncio import Redis

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        pytest.skip("cần REDIS_URL để kiểm tra kho thu hồi dùng chung")

    jti = _decode_claims(user.token)["jti"]
    redis = Redis.from_url(redis_url, decode_responses=True)
    try:
        key = f"fuurin:revoked_jti:{jti}"
        assert await redis.exists(key) == 0, "token chưa đăng xuất mà đã bị thu hồi"

        r = await client.post("/api/users/logout", headers=user.headers)
        assert r.status_code == 200, r.text

        assert await redis.exists(key) == 1, "đăng xuất KHÔNG ghi vào Redis -> sẽ mất khi restart backend"
        ttl = await redis.ttl(key)
        assert 0 < ttl <= 15 * 60 + 5, f"TTL phải bằng hạn còn lại của access token, nhận {ttl}"
    finally:
        await redis.aclose()

    assert (await client.get("/api/users/getByToken", headers=user.headers)).status_code == 401
