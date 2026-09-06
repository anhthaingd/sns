import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw not in (None, "") else default
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# Thư mục gốc của service (server_python/), dùng để mọi đường dẫn file
# không phụ thuộc vào current working directory khi chạy uvicorn.
BASE_DIR = Path(__file__).resolve().parents[2]

PORT = _int_env("PORT", 3000)
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/social_app")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "secret")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", ACCESS_TOKEN_SECRET)
# Hỗ trợ nhiều origin, phân tách bằng dấu phẩy (dev + staging + docker network).
CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:5173")
CORS_ORIGINS = [o.strip() for o in CLIENT_URL.split(",") if o.strip()]

UPLOAD_ROOT = BASE_DIR / "public"

# --- Redis: nơi lưu trạng thái dùng chung giữa các tiến trình ---------------
# Blacklist token trước đây là một `set()` trong RAM tiến trình, nên mỗi lần
# restart/deploy là mọi token đã đăng xuất sống lại (đã kiểm chứng được).
REDIS_URL = os.getenv("REDIS_URL", "")

# --- Vòng đời token --------------------------------------------------------
# Access token ngắn để thiệt hại khi lộ là hữu hạn; refresh token dài nhưng
# nằm trong cookie httpOnly (JavaScript không đọc được) và thu hồi được.
ACCESS_TOKEN_TTL_SECONDS = _int_env("ACCESS_TOKEN_TTL_SECONDS", 15 * 60)
REFRESH_TOKEN_TTL_SECONDS = _int_env("REFRESH_TOKEN_TTL_SECONDS", 7 * 24 * 60 * 60)

REFRESH_COOKIE_NAME = "refresh_token"
# Cookie chỉ được gửi kèm cho nhóm route auth, không đính vào mọi request.
REFRESH_COOKIE_PATH = "/api/users"
# Bật khi deploy sau HTTPS. Hai domain khác nhau còn cần SameSite=None.
COOKIE_SECURE = _bool_env("COOKIE_SECURE", False)
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

# --- Giới hạn tần suất cho các route nhạy cảm ------------------------------
# Đăng nhập chỉ đếm LẦN THẤT BẠI, trên hai chiều:
#   - theo email: chặn dò mật khẩu của một tài khoản cụ thể (chặt).
#   - theo IP:    chặn rải một mật khẩu phổ biến qua nhiều tài khoản.
LOGIN_FAIL_LIMIT_PER_EMAIL = _int_env("LOGIN_FAIL_LIMIT_PER_EMAIL", 10)
LOGIN_FAIL_LIMIT_PER_IP = _int_env("LOGIN_FAIL_LIMIT_PER_IP", 30)
LOGIN_RATE_LIMIT_WINDOW_SECONDS = _int_env("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 15 * 60)

# Đăng ký đếm mọi lần gọi (chặn tạo tài khoản rác hàng loạt).
REGISTER_RATE_LIMIT_MAX = _int_env("REGISTER_RATE_LIMIT_MAX", 60)
REGISTER_RATE_LIMIT_WINDOW_SECONDS = _int_env("REGISTER_RATE_LIMIT_WINDOW_SECONDS", 60 * 60)

REFRESH_RATE_LIMIT_MAX = _int_env("REFRESH_RATE_LIMIT_MAX", 120)
REFRESH_RATE_LIMIT_WINDOW_SECONDS = _int_env("REFRESH_RATE_LIMIT_WINDOW_SECONDS", 15 * 60)

# Log lỗi từ trình duyệt gửi lên (POST /api/client_logs). Endpoint này KHÔNG
# yêu cầu đăng nhập — lỗi có thể xảy ra ngay ở màn hình đăng nhập — nên giới
# hạn theo IP là chốt chặn duy nhất chống spam. Phía client cũng tự chặn: gộp
# trùng trong 30 giây và tối đa 50 bản ghi mỗi phiên.
CLIENT_LOG_RATE_LIMIT_MAX = _int_env("CLIENT_LOG_RATE_LIMIT_MAX", 60)
CLIENT_LOG_RATE_LIMIT_WINDOW_SECONDS = _int_env("CLIENT_LOG_RATE_LIMIT_WINDOW_SECONDS", 60)

# Chỉ bật khi backend thật sự nằm sau reverse proxy (nginx, Cloudflare...).
# Nếu bật mà KHÔNG có proxy, ai cũng tự đặt được header `X-Forwarded-For` và
# qua mặt giới hạn theo IP chỉ bằng cách đổi giá trị header mỗi lần gọi.
TRUST_PROXY_HEADERS = _bool_env("TRUST_PROXY_HEADERS", False)

# Cờ tắt toàn bộ giới hạn (chỉ dùng khi thật sự cần, ví dụ chạy tải thử).
RATE_LIMIT_ENABLED = _bool_env("RATE_LIMIT_ENABLED", True)

# --- Xếp hạng theo ngữ nghĩa -----------------------------------------------
# Service tính vector chạy riêng (xem thư mục embedder/). Để trống thì phần xếp
# hạng theo ngữ nghĩa tự tắt và hệ thống chấm điểm thuần bằng luật — vẫn dùng
# được, chỉ kém tinh tế hơn.
EMBEDDER_URL = os.getenv("EMBEDDER_URL", "")
EMBEDDER_TIMEOUT_SECONDS = _int_env("EMBEDDER_TIMEOUT_SECONDS", 30)

# --- Crawl ----------------------------------------------------------------
# Trang tuyển dụng cập nhật theo ngày; 10 phút là đủ mới mà vẫn cứu được người
# dùng khi nguồn chặn tạm thời (LinkedIn hay chặn khi bị gọi liên tục).
CRAWL_CACHE_TTL_SECONDS = _int_env("CRAWL_CACHE_TTL_SECONDS", 10 * 60)
# Mỗi trang mở thêm tốn RAM; 2 là mức an toàn cho container mặc định.
CRAWL_MAX_CONCURRENT_PAGES = _int_env("CRAWL_MAX_CONCURRENT_PAGES", 2)
CRAWL_NAVIGATION_TIMEOUT_MS = _int_env("CRAWL_NAVIGATION_TIMEOUT_MS", 30_000)
