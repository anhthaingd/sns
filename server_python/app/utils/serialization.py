"""Chuyển document Mongo/Beanie sang dict JSON-safe.

Trước đây mỗi controller tự viết một bản `_serialize_doc` riêng và mỗi bản
xử lý thiếu một kiểu khác nhau (bản của channels/posts không xử lý datetime
-> 500 trên mọi endpoint channel & post). Toàn bộ controller giờ dùng chung
hàm ở đây.
"""

from datetime import date, datetime
from typing import Any

from beanie import Document
from bson import ObjectId

# Field không bao giờ được trả ra API.
SENSITIVE_FIELDS = frozenset({"password"})


def to_jsonable(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    return value


def serialize_doc(doc: Any) -> dict | None:
    """Trả về dict JSON-safe, dùng khoá `_id` giống Mongoose để client không phải đổi."""
    if doc is None:
        return None

    if isinstance(doc, Document):
        data = doc.model_dump(by_alias=True)
    else:
        data = dict(doc)

    data = to_jsonable(data)

    if "id" in data:
        data["_id"] = data.pop("id")
    if "_id" in data:
        data["_id"] = str(data["_id"])

    for field in SENSITIVE_FIELDS:
        data.pop(field, None)

    return data
