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

from app.messages import message_for

logger = logging.getLogger("fuurin.error")

# Thông báo duy nhất được phép trả ra cho lỗi ngoài dự kiến. Chi tiết thật
# nằm trong log của server, không bao giờ đi ra ngoài.
GENERIC_SERVER_ERROR = message_for("server.generic")
INVALID_ID_MESSAGE = message_for("common.invalidId")


class ApiError(Exception):
    """Lỗi nghiệp vụ có chủ đích — thông báo an toàn để hiển thị cho người dùng.

    Hai cách dùng, cách thứ hai được ưu tiên::

        raise ApiError(409, "Địa chỉ email đã tồn tại!")          # cũ, còn chạy
        raise ApiError(409, code="auth.emailExists")              # nên dùng

    Đưa `code` vào thì câu tiếng Việt được lấy từ `app/messages.py`, và client
    có thứ để tra bản dịch (xem giải thích trong file đó). Tham số thay đổi
    được truyền qua `params` chứ KHÔNG ghép sẵn vào chuỗi — ghép sẵn là client
    hết đường dịch::

        raise ApiError(413, code="upload.tooLarge", params={"max": 5})
    """

    def __init__(
        self,
        status_code: int,
        message: str | None = None,
        *,
        code: str | None = None,
        params: dict | None = None,
    ):
        if message is None:
            if code is None:
                raise ValueError("ApiError cần `message` hoặc `code`")
            message = message_for(code, params)
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.params = params


def error_body(message: str, code: str | None = None, params: dict | None = None) -> dict[str, Any]:
    """Thân response lỗi.

    `code`/`params` chỉ xuất hiện khi có — thêm khoá `null` vào mọi lỗi chỉ làm
    payload rối mà client vẫn phải kiểm tra falsy.
    """
    body: dict[str, Any] = {"error": True, "success": False, "message": message}
    if code:
        body["code"] = code
    if params:
        body["params"] = params
    return body


def _json_error(status_code: int, message: str, code: str | None = None, params: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(message, code, params))


def _humanize_validation_error(exc: RequestValidationError) -> tuple[str, str, dict | None]:
    """Biến lỗi Pydantic thành (câu tiếng Việt, mã, tham số).

    Không lộ cấu trúc nội bộ của Pydantic ra ngoài; chỉ giữ tên trường.
    """
    errors = exc.errors()
    if not errors:
        return message_for("common.invalidPayload"), "common.invalidPayload", None

    fields = []
    for err in errors:
        # loc thường là ("body", "email") — bỏ phần vị trí, chỉ giữ tên trường.
        parts = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path", "header")]
        if parts:
            fields.append(".".join(parts))

    if not fields:
        return message_for("common.invalidPayload"), "common.invalidPayload", None
    params = {"fields": ", ".join(dict.fromkeys(fields))}
    return message_for("common.invalidPayloadFields", params), "common.invalidPayloadFields", params


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
            await _json_error(500, GENERIC_SERVER_ERROR, "server.generic")(scope, receive, send)


async def _api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return _json_error(exc.status_code, exc.message, exc.code, exc.params)


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or GENERIC_SERVER_ERROR)
    else:
        message = str(detail) if detail else GENERIC_SERVER_ERROR
    return _json_error(exc.status_code, message)


async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    message, code, params = _humanize_validation_error(exc)
    return _json_error(422, message, code, params)


async def _invalid_id_handler(_: Request, exc: InvalidId) -> JSONResponse:
    # Lưới an toàn: nơi nào quên dùng `to_object_id()` cũng không rò thông báo
    # của bson ("... is not a valid ObjectId, it must be a 12-byte input...").
    # WARNING chu khong phai INFO: toi day nghia la co cho quen dung
    # `to_object_id()`, tuc la con mot duong ro thong bao cua driver.
    logger.warning("InvalidId lot toi handler (thieu to_object_id o dau do): %s", exc)
    return _json_error(400, INVALID_ID_MESSAGE, "common.invalidId")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(InvalidId, _invalid_id_handler)
