import logging
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.config.settings import CORS_ORIGINS, PORT, REDIS_URL, UPLOAD_ROOT
from app.errors import CatchAllErrorMiddleware, register_error_handlers
from app.routes.channels import router as channels_router
from app.routes.chat import router as chat_router
from app.routes.jobs import router as jobs_router
from app.routes.match import router as match_router
from app.routes.notifications import router as notifications_router
from app.routes.posts import router as posts_router
from app.routes.shortcuts import router as shortcuts_router
from app.routes.users import router as users_router
from app.routes.web import router as web_router
from app.services.browser import browser_service
from app.services.embedding import close_embedder
from app.sockets.handlers import register_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("fuurin.main")

# Có Redis thì Socket.io phát sự kiện qua pub/sub, nên nhiều worker/nhiều
# instance vẫn gửi được tin tới đúng người. Không có thì chạy một tiến trình
# như cũ.
_socket_manager = socketio.AsyncRedisManager(REDIS_URL) if REDIS_URL else None

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=CORS_ORIGINS,
    client_manager=_socket_manager,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    await connect_redis()
    try:
        # Khởi động sẵn Chromium để request crawl đầu tiên không phải chờ
        # 1-2 giây. Lỗi ở đây không được phép làm app không lên được: mọi
        # chức năng khác vẫn dùng bình thường khi không có browser.
        await browser_service.start()
    except Exception:
        logger.exception("Không khởi động sẵn được browser, sẽ thử lại khi có request crawl")
    yield
    await close_embedder()
    await browser_service.stop()
    await close_redis()
    await close_db()


app = FastAPI(title="Fuurin API", lifespan=lifespan)

# Thứ tự quan trọng: middleware thêm SAU nằm NGOÀI. Thêm catch-all trước rồi
# CORS sau -> CORS bọc ngoài -> response 500 do catch-all sinh ra vẫn có header
# CORS, nên trình duyệt đọc được `message` và client hiện toast thay vì báo
# "network error".
app.add_middleware(CatchAllErrorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(channels_router)
app.include_router(posts_router)
app.include_router(notifications_router)
app.include_router(chat_router)
app.include_router(shortcuts_router)
app.include_router(web_router)
app.include_router(jobs_router)
app.include_router(match_router)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
(UPLOAD_ROOT / "uploads").mkdir(exist_ok=True)
(UPLOAD_ROOT / "certificates").mkdir(exist_ok=True)
app.mount("/public", StaticFiles(directory=UPLOAD_ROOT), name="public")

register_handlers(sio)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=PORT, reload=True)
