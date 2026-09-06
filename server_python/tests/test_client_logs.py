"""Endpoint nhận log lỗi từ trình duyệt.

Đây là endpoint MỞ (không cần đăng nhập) vì lỗi có thể xảy ra ngay ở màn hình
đăng nhập. Vì vậy các test dưới đây tập trung vào chuyện nó không trở thành lỗ
hổng: dữ liệu quá khổ bị chặn, mức log lạ bị chặn.
"""

import httpx
import pytest

pytestmark = pytest.mark.asyncio


async def test_accepts_a_browser_error_without_login(client: httpx.AsyncClient):
    res = await client.post(
        "/api/client_logs",
        json={
            "level": "error",
            "event": "render.crash",
            "message": "Cannot read properties of null",
            "url": "/search?tab=posts",
            "stack": "at Posts.jsx:84",
        },
    )
    assert res.status_code == 202, res.text
    assert res.json()["success"] is True


async def test_missing_fields_fall_back_to_defaults(client: httpx.AsyncClient):
    """Log là việc phụ: thiếu field thì vẫn nhận, không bắt client gửi lại."""
    res = await client.post("/api/client_logs", json={})
    assert res.status_code == 202, res.text


async def test_rejects_oversized_stack(client: httpx.AsyncClient):
    """Không có giới hạn thì một stack trace 10MB đi thẳng vào log của server."""
    res = await client.post(
        "/api/client_logs",
        json={"level": "error", "event": "x", "message": "y", "stack": "A" * 5000},
    )
    assert res.status_code == 422


async def test_rejects_unknown_level(client: httpx.AsyncClient):
    """Chỉ nhận error/warn — không cho client tự chọn mức log tuỳ ý."""
    res = await client.post("/api/client_logs", json={"level": "critical", "event": "x"})
    assert res.status_code == 422


async def test_newlines_in_message_do_not_break_a_log_line(client: httpx.AsyncClient):
    """Chèn xuống dòng là cách giả mạo một dòng log trông như của hệ thống."""
    res = await client.post(
        "/api/client_logs",
        json={"level": "warn", "event": "spoof", "message": "binh thuong\nERROR gia mao"},
    )
    assert res.status_code == 202
