from fastapi import APIRouter, Depends, Header, Request

from app.config.settings import (
    CLIENT_LOG_RATE_LIMIT_MAX,
    CLIENT_LOG_RATE_LIMIT_WINDOW_SECONDS,
)
from app.controllers.client_logs import record_client_log
from app.schemas.requests import ClientLogRequest
from app.schemas.responses import ERROR_RESPONSES, MessageResponse
from app.services.rate_limit import client_ip, rate_limit

router = APIRouter(tags=["client-logs"], responses=ERROR_RESPONSES)

# Không yêu cầu đăng nhập: lỗi có thể xảy ra ngay ở trang đăng nhập, mà đó lại
# đúng là lúc cần log nhất. Đổi lại, giới hạn theo IP là bắt buộc.
client_log_rate_limit = Depends(
    rate_limit("client_logs", CLIENT_LOG_RATE_LIMIT_MAX, CLIENT_LOG_RATE_LIMIT_WINDOW_SECONDS)
)


@router.post(
    "/api/client_logs",
    status_code=202,
    response_model=MessageResponse,
    dependencies=[client_log_rate_limit],
)
async def route_client_log(
    body: ClientLogRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
):
    return await record_client_log(body, client_ip(request), user_agent)
