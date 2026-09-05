import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Thư mục gốc của service (server_python/), dùng để mọi đường dẫn file
# không phụ thuộc vào current working directory khi chạy uvicorn.
BASE_DIR = Path(__file__).resolve().parents[2]

PORT = int(os.getenv("PORT", "3000"))
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/social_app")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "secret")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", ACCESS_TOKEN_SECRET)
# Hỗ trợ nhiều origin, phân tách bằng dấu phẩy (dev + staging + docker network).
CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:5173")
CORS_ORIGINS = [o.strip() for o in CLIENT_URL.split(",") if o.strip()]

UPLOAD_ROOT = BASE_DIR / "public"
