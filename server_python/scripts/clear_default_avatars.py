"""Gỡ ảnh đại diện mặc định khỏi các tài khoản đã có trong DB.

    docker compose run --rm server python -m scripts.clear_default_avatars
    docker compose run --rm server python -m scripts.clear_default_avatars --dry-run

Trước đây `app/models/user.py` gán sẵn cho mọi tài khoản mới một file dùng
chung — `avatar-trang.jpg`, hình bóng người xám. Vì trường `avatar` luôn có giá
trị nên nhánh dựng ảnh thay thế bằng chữ cái đầu tên trong
`client/src/components/ui/Avatar.jsx` không bao giờ chạy, và trong mọi danh
sách mọi người trông giống hệt nhau.

Model nay để trống mặc định, nhưng điều đó chỉ áp dụng cho tài khoản TẠO MỚI.
Script này gỡ trường đó khỏi những tài khoản cũ vẫn đang trỏ vào file mặc định.

CHỈ đụng tới đúng file mặc định: ai đã tự tải ảnh lên thì giữ nguyên.
"""

import argparse
import asyncio
import logging
import sys

from app.config.database import close_db, connect_db
from app.models.user import User

logger = logging.getLogger("fuurin.avatars")

DEFAULT_NAMES = {"avatar_trang.jpg", "avatar-trang.jpg"}
DEFAULT_URLS = {"public/avatar-trang.jpg", "/public/avatar-trang.jpg"}


def is_default(avatar: dict | None) -> bool:
    if not avatar:
        return False
    return avatar.get("name") in DEFAULT_NAMES or avatar.get("url") in DEFAULT_URLS


async def clear(dry_run: bool) -> dict:
    collection = User.get_motor_collection()
    total = await collection.count_documents({})
    targets = [doc async for doc in collection.find({"avatar": {"$ne": None}}, {"avatar": 1})]
    hits = [doc["_id"] for doc in targets if is_default(doc.get("avatar"))]

    if hits and not dry_run:
        await collection.update_many({"_id": {"$in": hits}}, {"$unset": {"avatar": ""}})

    logger.info("tổng %d tài khoản, %d dùng ảnh mặc định", total, len(hits))
    return {"total": total, "cleared": len(hits)}


async def main() -> int:
    parser = argparse.ArgumentParser(description="Go anh dai dien mac dinh khoi tai khoan cu")
    parser.add_argument("--dry-run", action="store_true", help="Chi dem, khong ghi")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await connect_db()
    try:
        result = await clear(args.dry_run)
    finally:
        await close_db()

    verb = "se go" if args.dry_run else "da go"
    print(f"Tai khoan: {result['total']} | {verb}: {result['cleared']}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
