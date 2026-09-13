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

# --- Lời khuyên bằng LLM ---------------------------------------------------
# Xem docs/12-loi-khuyen-bang-llm.md. Phần này CHỈ viết lời khuyên; điểm số và
# việc phát hiện thiếu sót vẫn 100% do app/services/matching.py quyết định.
#
# Không có key thì tính năng tự tắt: endpoint vẫn trả 200 kèm `advice: null`,
# giao diện ẩn thẻ gợi ý. Giống hệt cách EMBEDDER_URL trống làm phần xếp hạng
# ngữ nghĩa tự tắt mà không màn hình nào báo lỗi.
LLM_ENABLED = _bool_env("LLM_ENABLED", True)

# Tên model CỐ Ý nằm ở biến môi trường. Đo ngày 13/09/2026: hai tên model chọn
# lúc thiết kế (`gemini-2.5-flash`, `llama-3.3-70b-versatile`) đều đã 404 —
# một cái "không còn mở cho người dùng mới", một cái bị gỡ hẳn. Ghim tên model
# vào code là hẹn giờ cho một lỗi khó hiểu sau vài tháng.
LLM_PRIMARY_BASE_URL = os.getenv("LLM_PRIMARY_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
LLM_PRIMARY_MODEL = os.getenv("LLM_PRIMARY_MODEL", "gemini-3.1-flash-lite")
LLM_PRIMARY_API_KEY = os.getenv("GEMINI_API_KEY", "")

LLM_FALLBACK_BASE_URL = os.getenv("LLM_FALLBACK_BASE_URL", "https://api.groq.com/openai/v1")
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "qwen/qwen3.8-27b")
LLM_FALLBACK_API_KEY = os.getenv("GROQ_API_KEY", "")

LLM_TIMEOUT_SECONDS = _int_env("LLM_TIMEOUT_SECONDS", 12)

# Rộng rãi có chủ đích. Model có bước "suy nghĩ" tiêu hết hạn mức cho phần nghĩ
# rồi trả về JSON bị cắt ngang — đo được: gemini-3.5-flash tốn 1200-1600 token
# nghĩ để viết ra 200 token. Hạn mức thừa không tốn gì, thiếu thì hỏng âm thầm.
LLM_MAX_TOKENS = _int_env("LLM_MAX_TOKENS", 2000)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Cache 7 ngày. Khoá băm từ chính dữ liệu đầu vào nên sửa CV là khoá đổi theo,
# không bao giờ phải xoá cache thủ công.
LLM_CACHE_TTL_SECONDS = _int_env("LLM_CACHE_TTL_SECONDS", 7 * 24 * 3600)

# Chặn một người bấm loạn đốt hết hạn mức của cả hệ thống.
LLM_USER_RATE_LIMIT_MAX = _int_env("LLM_USER_RATE_LIMIT_MAX", 20)
LLM_USER_RATE_LIMIT_WINDOW_SECONDS = _int_env("LLM_USER_RATE_LIMIT_WINDOW_SECONDS", 3600)

# Chốt chặn cuối để không vượt gói miễn phí.
LLM_DAILY_MAX = _int_env("LLM_DAILY_MAX", 400)

# Cầu dao: hỏng liên tiếp bấy nhiêu lần thì ngừng gọi nhà cung cấp đó một lúc.
# Hết hạn mức ngày là trạng thái kéo dài hàng giờ — không có cầu dao thì mọi
# request sau đó vẫn phải chờ hết timeout rồi mới bỏ cuộc.
LLM_BREAKER_THRESHOLD = _int_env("LLM_BREAKER_THRESHOLD", 3)
LLM_BREAKER_COOLDOWN_SECONDS = _int_env("LLM_BREAKER_COOLDOWN_SECONDS", 15 * 60)


# --- Crawl ----------------------------------------------------------------
# Trang tuyển dụng cập nhật theo ngày; 10 phút là đủ mới mà vẫn cứu được người
# dùng khi nguồn chặn tạm thời (LinkedIn hay chặn khi bị gọi liên tục).
CRAWL_CACHE_TTL_SECONDS = _int_env("CRAWL_CACHE_TTL_SECONDS", 10 * 60)
# Mỗi trang mở thêm tốn RAM; 2 là mức an toàn cho container mặc định.
CRAWL_MAX_CONCURRENT_PAGES = _int_env("CRAWL_MAX_CONCURRENT_PAGES", 2)
CRAWL_NAVIGATION_TIMEOUT_MS = _int_env("CRAWL_NAVIGATION_TIMEOUT_MS", 30_000)
