"""E2E chạy Playwright trên frontend React thật, gọi backend FastAPI thật."""
import os
import uuid

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from pymongo import AsyncMongoClient

APP_URL = os.getenv("APP_URL", "http://localhost:5173")
API_URL = os.getenv("API_URL", "http://localhost:3000")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/fuurin")
ARTIFACTS = os.getenv("ARTIFACTS_DIR", "/artifacts")

PASSWORD = "Passw0rd!"


def unique_email(prefix="e2e"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


@pytest_asyncio.fixture
async def browser():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        yield b
        await b.close()


@pytest_asyncio.fixture
async def db():
    mongo = AsyncMongoClient(MONGO_URL)
    yield mongo[MONGO_URL.rsplit("/", 1)[-1]]
    await mongo.close()


@pytest_asyncio.fixture
async def page(browser, request):
    ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
    pg = await ctx.new_page()

    console_errors = []
    pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: console_errors.append(str(e)))
    pg.console_errors = console_errors

    yield pg

    os.makedirs(ARTIFACTS, exist_ok=True)
    await pg.screenshot(path=f"{ARTIFACTS}/{request.node.name}.png", full_page=True)
    await ctx.close()


async def register_via_ui(page, email, username="e2e user"):
    await page.goto(f"{APP_URL}/register", wait_until="domcontentloaded")
    await page.get_by_placeholder("Enter your name...").wait_for(timeout=30000)
    await page.get_by_placeholder("Enter your name...").fill(username)
    await page.get_by_placeholder("Enter your email...").fill(email)
    await page.get_by_placeholder("Enter your password...").fill(PASSWORD)
    await page.get_by_role("button", name="Register", exact=True).click()
    # Form đăng ký chỉ hiện toast thành công, không tự chuyển trang.
    await page.wait_for_selector("text=Tạo tài khoản thành công!", timeout=20000)


async def login_via_ui(page, email):
    await page.goto(f"{APP_URL}/login", wait_until="domcontentloaded")
    await page.get_by_placeholder("Enter your email...").wait_for(timeout=30000)
    await page.get_by_placeholder("Enter your email...").fill(email)
    await page.get_by_placeholder("Enter your password...").fill(PASSWORD)
    await page.get_by_role("button", name="Login").click()
    await page.wait_for_url(f"{APP_URL}/", timeout=20000)


async def promote_to_admin(db, email):
    role = await db.roles.find_one({"value": 1})
    await db.users.update_one({"email": email}, {"$set": {"role": role["_id"]}})
