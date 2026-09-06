"""Chuyển chuỗi sang ObjectId một cách an toàn.

`ObjectId("abc")` ném `bson.errors.InvalidId` với thông báo mô tả cấu trúc nội
bộ của driver. Trước đây thông báo đó đi thẳng ra client qua
`except Exception as e: message = str(e)`. Hàm ở đây đổi thành lỗi nghiệp vụ
có thông báo an toàn, đồng thời nói rõ trường nào sai để người dùng hiểu.
"""

from bson import ObjectId
from bson.errors import InvalidId

from app.errors import ApiError


def to_object_id(value, field: str = "id") -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    # Bẫy dễ sập: `ObjectId(None)` KHÔNG ném lỗi mà sinh ra một id mới ngẫu
    # nhiên. Nếu để lọt, một tham số thiếu sẽ lặng lẽ biến thành truy vấn theo
    # id không tồn tại (404 khó hiểu) thay vì báo sai dữ liệu đầu vào.
    if not isinstance(value, (str, bytes)) or not value:
        raise ApiError(400, code="common.invalidValue", params={"field": field})
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as err:
        raise ApiError(400, code="common.invalidValue", params={"field": field}) from err


def to_object_id_or_none(value, field: str = "id") -> ObjectId | None:
    if value in (None, "", "null", "undefined"):
        return None
    return to_object_id(value, field)
