"""Hệ thống xử lý lỗi tập trung cho toàn bộ API.

Trước đây mỗi controller tự bắt `except Exception as e` rồi trả `str(e)` cho
client — vừa lặp 51 lần, vừa rò chi tiết nội bộ (tên collection, câu truy vấn,
thông báo của driver Mongo). Giờ controller chỉ cần `raise ApiError(...)` cho
lỗi nghiệp vụ và **không bắt** lỗi ngoài dự kiến; mọi thứ đổ về đây.

Hợp đồng bất di bất dịch: mọi response lỗi có đúng hình dạng

    {"error": true, "success": false, "message": "..."}

vì client đọc `error.data.message` ở 24 chỗ để hiện toast. `HTTPException` mặc
định của FastAPI trả `{"detail": ...}` nên KHÔNG được dùng trực tiếp.
"""

import logging
from typing import Any

from bson.errors import InvalidId
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("fuurin.error")

# Thông báo duy nhất được phép trả ra cho lỗi ngoài dự kiến. Chi tiết thật
# nằm trong log của server, không bao giờ đi ra ngoài.
GENERIC_SERVER_ERROR = "Đã có lỗi xảy ra, vui lòng thử lại sau!"
INVALID_ID_MESSAGE = "Định danh không hợp lệ!"


class ApiError(Exception):
    """Lỗi nghiệp vụ có chủ đích — thông báo an toàn để hiển thị cho người dùng."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def error_body(message: str) -> dict[str, Any]:
    return {"error": True, "success": False, "message": message}


def _json_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(message))


def _humanize_validation_error(exc: RequestValidationError) -> str:
    """Biến lỗi Pydantic thành một câu tiếng Việt gọn, không lộ cấu trúc nội bộ."""
    errors = exc.errors()
    if not errors:
        return "Dữ liệu gửi lên không hợp lệ!"

    fields = []
    for err in errors:
        # loc thường là ("body", "email") — bỏ phần vị trí, chỉ giữ tên trường.
        parts = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path", "header")]
        if parts:
            fields.append(".".join(parts))

    if not fields:
        return "Dữ liệu gửi lên không hợp lệ!"
    unique_fields = list(dict.fromkeys(fields))
    return f"Dữ liệu gửi lên không hợp lệ ở: {', '.join(unique_fields)}"


class CatchAllErrorMiddleware:
    """Chốt chặn cuối cho lỗi không được handler nào bắt.

    Phải là middleware chứ không phải `add_exception_handler(Exception, ...)`:
    handler cho `Exception` được Starlette gắn vào `ServerErrorMiddleware` —
    lớp NGOÀI CÙNG, nằm ngoài `CORSMiddleware`. Response 500 sinh ra ở đó sẽ
    thiếu header CORS, trình duyệt báo "network error" và toast của client
    không bao giờ hiện. Đặt ở đây (bên trong CORS) thì header được thêm đúng.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception("Unhandled error on %s %s", scope.get("method"), scope.get("path"))
            if response_started:
                # Đã gửi header đi rồi thì không thể thay bằng JSON được nữa.
                raise
            await _json_error(500, GENERIC_SERVER_ERROR)(scope, receive, send)


async def _api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return _json_error(exc.status_code, exc.message)


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or GENERIC_SERVER_ERROR)
    else:
        message = str(detail) if detail else GENERIC_SERVER_ERROR
    return _json_error(exc.status_code, message)


async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _json_error(422, _humanize_validation_error(exc))


async def _invalid_id_handler(_: Request, exc: InvalidId) -> JSONResponse:
    # Lưới an toàn: nơi nào quên dùng `to_object_id()` cũng không rò thông báo
    # của bson ("... is not a valid ObjectId, it must be a 12-byte input...").
    # WARNING chu khong phai INFO: toi day nghia la co cho quen dung
    # `to_object_id()`, tuc la con mot duong ro thong bao cua driver.
    logger.warning("InvalidId lot toi handler (thieu to_object_id o dau do): %s", exc)
    return _json_error(400, INVALID_ID_MESSAGE)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(InvalidId, _invalid_id_handler)
