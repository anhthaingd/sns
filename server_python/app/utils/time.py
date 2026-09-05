"""Thời điểm hiện tại theo UTC.

`datetime.utcnow()` đã bị đánh dấu deprecated, nhưng thay thẳng bằng
`datetime.now(timezone.utc)` thì sinh ra datetime CÓ timezone — trong khi mọi
document đang nằm trong DB đều là datetime KHÔNG timezone. Trộn hai loại lại
thì mọi phép so sánh ném `TypeError`. Hàm này lấy giờ UTC đúng cách rồi bỏ
timezone để giữ nguyên kiểu dữ liệu cũ.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
