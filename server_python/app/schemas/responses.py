"""Schema cho response — sinh tài liệu ở /docs và khoá hợp đồng với client.

**Chỉ mô tả tầng ngoài cùng, cố ý không mô tả phần tử bên trong danh sách.**
Lý do: `response_model` của FastAPI lọc bỏ mọi field không khai báo, và một số
quan hệ trong dữ liệu thật không có hình dạng cố định — ví dụ `post["user"]`
là object khi tác giả còn tồn tại nhưng vẫn là chuỗi id khi tài khoản đã bị
xoá. Khai báo chặt phần tử con sẽ vừa làm mất field, vừa ném 500 trên dữ liệu
cũ. Tầng ngoài (`posts`, `totalPage`, `accessToken`, ...) mới là thứ client
thật sự phụ thuộc, và `tests/test_response_contract.py` canh phần còn lại.

`extra="allow"` giữ nguyên mọi khoá phát sinh thêm thay vì âm thầm bỏ đi.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    error: bool = False
    success: bool = True


class MessageResponse(ApiEnvelope):
    message: str


class TokenResponse(ApiEnvelope):
    accessToken: str


class WebsiteResponse(ApiEnvelope):
    website: dict[str, Any] | None = None


# --- Người dùng ------------------------------------------------------------


class CurrentUserResponse(ApiEnvelope):
    user: dict[str, Any]
    followers: list[dict[str, Any]]
    following: list[dict[str, Any]]


class UserDetailsResponse(ApiEnvelope):
    user: dict[str, Any]
    followers: list[dict[str, Any]]
    following: list[dict[str, Any]]
    posts: int
    channels: int


class UserListResponse(ApiEnvelope):
    users: list[dict[str, Any]]
    totalPage: int
    totalUsers: int


class AdminUserListResponse(UserListResponse):
    curPage: int


class FollowersResponse(ApiEnvelope):
    # `user` vắng mặt khi tài khoản chưa có document followers.
    user: str | None = None
    followers: list[dict[str, Any]]
    totalPage: int


class FollowingResponse(ApiEnvelope):
    user: str | None = None
    following: list[dict[str, Any]]
    totalPage: int


class ResumeResponse(ApiEnvelope):
    resume: dict[str, Any] | None = None


# --- Channel ---------------------------------------------------------------


class ChannelListResponse(ApiEnvelope):
    channels: list[dict[str, Any]]
    totalPage: int
    curPage: int


class UserChannelsResponse(ApiEnvelope):
    channels: list[dict[str, Any]]


class ChannelDetailsResponse(ApiEnvelope):
    channel: dict[str, Any]


# --- Bài viết --------------------------------------------------------------


class PostListResponse(ApiEnvelope):
    posts: list[dict[str, Any]]
    totalPage: int


class HomePostListResponse(PostListResponse):
    totalPosts: int


class PostDetailsResponse(ApiEnvelope):
    post: dict[str, Any]


# --- Thông báo, shortcut, chat ---------------------------------------------


class NotificationListResponse(ApiEnvelope):
    notifications: list[dict[str, Any]]
    notRead: int
    totalPage: int


class ShortcutListResponse(ApiEnvelope):
    shortcuts: list[dict[str, Any]]


class NewestMessageResponse(ApiEnvelope):
    messages: list[dict[str, Any]]
    unread: int


class ChatResponse(ApiEnvelope):
    messages: list[dict[str, Any]]
    totalPage: int
    curPage: int


# --- Việc làm & doanh nghiệp -----------------------------------------------


class JobListResponse(ApiEnvelope):
    jobs: list[dict[str, Any]]
    totalPage: int
    totalJobs: int
    curPage: int


class JobDetailsResponse(ApiEnvelope):
    job: dict[str, Any]


class CompanyListResponse(ApiEnvelope):
    companies: list[dict[str, Any]]
    totalPage: int
    totalCompanies: int
    curPage: int


class CompanyDetailsResponse(ApiEnvelope):
    company: dict[str, Any]
    jobs: list[dict[str, Any]]


class JobFiltersResponse(ApiEnvelope):
    prefectures: list[str]
    japaneseLevels: list[str]
    skills: list[dict[str, Any]]


class MarketResponse(ApiEnvelope):
    totalJobs: int
    minGroupSize: int
    skills: list[dict[str, Any]]
    japanese: list[dict[str, Any]]
    prefectures: list[dict[str, Any]]


# --- Gợi ý & phân tích thiếu sót --------------------------------------------


class CompanyMatchResponse(ApiEnvelope):
    matches: list[dict[str, Any]]
    totalPage: int
    totalCompanies: int
    curPage: int
    # Nói rõ phần xếp hạng theo ngữ nghĩa có đang hoạt động hay không, để giao
    # diện không tỏ ra thông minh hơn thực tế khi embedder tắt.
    semanticAvailable: bool


class JobMatchResponse(ApiEnvelope):
    matches: list[dict[str, Any]]
    totalPage: int
    totalJobs: int
    curPage: int
    semanticAvailable: bool


class GapResponse(ApiEnvelope):
    job: dict[str, Any]
    company: dict[str, Any] | None = None
    match: dict[str, Any]
    qualified: bool


class CompanyGapResponse(ApiEnvelope):
    company: dict[str, Any]
    bestJob: dict[str, Any]
    bestMatch: dict[str, Any]
    positions: list[dict[str, Any]]
    combinedGaps: list[dict[str, Any]]


class WhatIfSuggestionsResponse(ApiEnvelope):
    totalJobs: int
    baseline: dict[str, Any]
    suggestions: list[dict[str, Any]]


class WhatIfSimulateResponse(ApiEnvelope):
    baseline: dict[str, Any]
    combined: dict[str, Any]
    sumOfIndividualDeltas: int


# --- Quản trị ---------------------------------------------------------------


class EtlStatusResponse(ApiEnvelope):
    status: dict[str, Any]
    stats: dict[str, Any]
    sources: list[str]


# Hình dạng lỗi dùng chung — khai báo để /docs hiện đúng thứ client phải đọc.
class ErrorResponse(BaseModel):
    error: bool = True
    success: bool = False
    message: str


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Dữ liệu gửi lên không hợp lệ"},
    401: {"model": ErrorResponse, "description": "Chưa đăng nhập hoặc token đã bị thu hồi"},
    403: {"model": ErrorResponse, "description": "Không đủ quyền"},
    404: {"model": ErrorResponse, "description": "Không tìm thấy"},
    409: {"model": ErrorResponse, "description": "Xung đột dữ liệu"},
    422: {"model": ErrorResponse, "description": "Sai kiểu dữ liệu"},
    429: {"model": ErrorResponse, "description": "Thao tác quá nhiều lần"},
    500: {"model": ErrorResponse, "description": "Lỗi hệ thống"},
}
