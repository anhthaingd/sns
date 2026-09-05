"""
Integration test cho API Fuurin: gọi thẳng vào server đang chạy.

Chạy:
    BASE_URL=http://server:3000 MONGO_URL=mongodb://mongo:27017/fuurin pytest
"""

import os
import uuid

import httpx
import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/fuurin")


def unique_email(prefix="user"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as c:
        yield c


@pytest_asyncio.fixture
async def db():
    mongo = AsyncMongoClient(MONGO_URL)
    yield mongo[MONGO_URL.rsplit("/", 1)[-1]]
    await mongo.close()


async def _register_and_login(client, email, password="Passw0rd!", username=None):
    r = await client.post(
        "/api/users/register",
        json={"email": email, "password": password, "username": username or email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    r = await client.post("/api/users/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["accessToken"]


class Actor:
    """Một user đã đăng nhập + header Authorization sẵn sàng."""

    def __init__(self, email, token, user_id=None):
        self.email = email
        self.token = token
        self.id = user_id

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}


@pytest_asyncio.fixture
async def user(client, db):
    email = unique_email("user")
    token = await _register_and_login(client, email)
    doc = await db.users.find_one({"email": email})
    return Actor(email, token, str(doc["_id"]))


@pytest_asyncio.fixture
async def other_user(client, db):
    email = unique_email("other")
    token = await _register_and_login(client, email)
    doc = await db.users.find_one({"email": email})
    return Actor(email, token, str(doc["_id"]))


@pytest_asyncio.fixture
async def admin(client, db):
    """Đăng ký user rồi nâng quyền admin trong DB, sau đó login lại để token mang role mới."""
    email = unique_email("admin")
    password = "Passw0rd!"
    await _register_and_login(client, email, password)

    admin_role = await db.roles.find_one({"value": 1})
    assert admin_role is not None, "DB chưa seed roles"
    await db.users.update_one({"email": email}, {"$set": {"role": admin_role["_id"]}})

    r = await client.post("/api/users/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    doc = await db.users.find_one({"email": email})
    return Actor(email, r.json()["accessToken"], str(doc["_id"]))


@pytest_asyncio.fixture
async def channel(client, admin):
    """Channel do admin tạo, kèm ảnh background."""
    name = f"channel-{uuid.uuid4().hex[:8]}"
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
        "00000049454e44ae426082"
    )
    r = await client.post(
        "/api/channels",
        headers=admin.headers,
        data={"name": name, "intro": "test channel"},
        files={"images": ("bg.png", png, "image/png")},
    )
    assert r.status_code == 201, r.text
    r = await client.get("/api/channels", params={"search": name})
    assert r.status_code == 200, r.text
    created = next(c for c in r.json()["channels"] if c["name"] == name)
    return created


@pytest_asyncio.fixture
async def has_jobs(db):
    """Bỏ qua khi DB chưa chạy ETL — test này nói về API, không phải về crawl."""
    if await db.jobs.count_documents({"is_active": True}) == 0:
        pytest.skip("chưa có dữ liệu việc làm, chạy `scripts.run_etl` trước")
    return True


@pytest_asyncio.fixture
async def user_with_resume(client, user):
    """User đã có CV — điều kiện để dùng chức năng gợi ý."""
    r = await client.post(
        "/api/resume",
        headers=user.headers,
        data={
            "name": "Nguyen Van A",
            "position": "Backend Engineer",
            "skills": '["Python", "Docker", "AWS"]',
            "languages": '["Japanese N2", "English business level"]',
            "experiences": '[{"name":"ABC","startTime":"2021-04","endTime":"2025-03","position":"Backend Engineer","description":"Python FastAPI"}]',
        },
    )
    assert r.status_code == 200, r.text
    return user
