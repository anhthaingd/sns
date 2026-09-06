"""Nhận log lỗi từ trình duyệt và đổ vào log của backend.

Vì sao tồn tại: lỗi phía frontend trước đây chỉ nằm trong console máy người
dùng. Có endpoint này thì `docker compose logs server` là chỗ duy nhất cần xem
khi ai đó báo "web bị lỗi", thay vì phải bảo họ mở DevTools chụp màn hình.

Đây KHÔNG phải hệ thống giám sát: không lưu DB, không thống kê. Chỉ ghi ra
stdout — vừa đủ để lần ra một sự cố, và không phát sinh thứ gì phải bảo trì.
"""

import logging

from app.schemas.requests import ClientLogRequest
from app.utils.responses import ok

# Tên logger riêng để lọc nhanh: `docker compose logs server | grep fuurin.client`
logger = logging.getLogger("fuurin.client")

_LEVELS = {"error": logging.ERROR, "warn": logging.WARNING}


def _one_line(value: str | None, limit: int) -> str:
    """Ép về một dòng: log nhiều dòng làm hỏng việc grep và có thể bị giả mạo.

    Stack trace do client gửi lên chứa ký tự xuống dòng; để nguyên thì kẻ xấu
    có thể chèn dòng trông như log thật của hệ thống.
    """
    if not value:
        return ""
    return value.replace("\r", " ").replace("\n", " ⏎ ")[:limit]


async def record_client_log(body: ClientLogRequest, ip: str, user_agent: str | None = None):
    logger.log(
        _LEVELS.get(body.level, logging.WARNING),
        "[%s] %s | %s | url=%s | ip=%s | ua=%s%s",
        body.level,
        _one_line(body.event, 100),
        _one_line(body.message, 500),
        _one_line(body.url, 300) or "-",
        ip,
        _one_line(user_agent, 120) or "-",
        f" | stack={_one_line(body.stack, 2000)}" if body.stack else "",
    )
    # Trả về nhanh và không tiết lộ gì: client chỉ cần biết là đã nhận.
    return ok(code="log.received")
