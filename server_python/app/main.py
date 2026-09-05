from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.database import close_db, connect_db
from app.config.settings import CORS_ORIGINS, PORT, UPLOAD_ROOT
from app.routes.channels import router as channels_router
from app.routes.chat import router as chat_router
from app.routes.crawl import router as crawl_router
from app.routes.notifications import router as notifications_router
from app.routes.posts import router as posts_router
from app.routes.shortcuts import router as shortcuts_router
from app.routes.users import router as users_router
from app.routes.web import router as web_router
from app.sockets.handlers import register_handlers

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=CORS_ORIGINS,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="Fuurin API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(crawl_router)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
(UPLOAD_ROOT / "uploads").mkdir(exist_ok=True)
(UPLOAD_ROOT / "certificates").mkdir(exist_ok=True)
app.mount("/public", StaticFiles(directory=UPLOAD_ROOT), name="public")

register_handlers(sio)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:socket_app", host="0.0.0.0", port=PORT, reload=True)
