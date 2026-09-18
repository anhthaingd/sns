"""Nạp roles + cấu hình website — dữ liệu bắt buộc để đăng ký/đăng nhập chạy được.

Không import FastAPI/settings nên chỉ cần `pymongo` + `DATABASE_URL`.
An toàn khi chạy lại: upsert theo tên, không xoá user/post đã có.

    DATABASE_URL='mongodb+srv://user:pass@cluster.mongodb.net/fuurin' \\
      python -m scripts.seed_required

Hoặc từ thư mục gốc repo:

    DATABASE_URL='...' python server_python/scripts/seed_required.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DEFAULT_DB_NAME = "fuurin"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _database_name(url: str) -> str:
    path = urlsplit(url).path.lstrip("/")
    name = path.split("?", 1)[0]
    return name or DEFAULT_DB_NAME


def _load_json(name: str) -> list:
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def _as_oid(value):
    if isinstance(value, dict) and "$oid" in value:
        return ObjectId(value["$oid"])
    return value


def seed(url: str) -> None:
    db = MongoClient(url, serverSelectionTimeoutMS=15000)[_database_name(url)]

    roles = 0
    for raw in _load_json("roles.json"):
        name = raw["name"]
        db.roles.update_one(
            {"name": name},
            {
                "$set": {"name": name, "value": raw["value"]},
                "$setOnInsert": {"_id": _as_oid(raw.get("_id"))},
            },
            upsert=True,
        )
        roles += 1

    webs = 0
    for raw in _load_json("social_app.webs.json"):
        name = raw.get("website_name") or "Fuurin"
        db.webs.update_one(
            {"website_name": name},
            {
                "$set": {
                    "website_name": name,
                    "logo": raw.get("logo"),
                    "website_quotes_register": raw.get("website_quotes_register"),
                    "website_quotes_login": raw.get("website_quotes_login"),
                    "color_title": raw.get("color_title"),
                },
                "$setOnInsert": {"_id": _as_oid(raw.get("_id"))},
            },
            upsert=True,
        )
        webs += 1

    print(f"Seed xong: {roles} roles, {webs} website config → {_database_name(url)}")


def main() -> int:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("Thiếu DATABASE_URL. Ví dụ:", file=sys.stderr)
        print(
            "  DATABASE_URL='mongodb+srv://user:pass@host/fuurin' python -m scripts.seed_required",
            file=sys.stderr,
        )
        return 1
    try:
        seed(url)
    except PyMongoError as exc:
        print(f"Không kết nối / ghi được MongoDB: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
