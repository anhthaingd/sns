"""Chạy ETL từ giao diện quản trị.

Chạy nền chứ không chặn request: một mẻ ETL đầy đủ mất vài phút, giữ kết nối
HTTP suốt thời gian đó sẽ timeout ở proxy hoặc trình duyệt.

Trạng thái lưu trong Redis để mọi tiến trình backend cùng nhìn thấy — nếu để
trong RAM thì bấm "chạy" ở worker này mà xem trạng thái ở worker khác là không
thấy gì.
"""

import asyncio
import json
import logging

from app.config.redis_client import get_redis
from app.errors import ApiError
from app.models.company import Company
from app.models.job import Job
from app.services.etl.parsers import SOURCES
from app.services.etl.pipeline import run_etl
from app.utils.permissions import require_admin
from app.utils.responses import ok
from app.utils.time import utc_now

logger = logging.getLogger("fuurin.admin.etl")

STATUS_KEY = "fuurin:etl:status"
# Giữ trạng thái đủ lâu để xem lại sau khi chạy xong, nhưng không giữ mãi.
STATUS_TTL_SECONDS = 24 * 60 * 60

# Chặn chạy hai mẻ cùng lúc: hai mẻ song song sẽ tranh nhau mở trình duyệt và
# ghi đè lẫn nhau. Khoá tự hết hạn để một lần crash không khoá vĩnh viễn.
LOCK_KEY = "fuurin:etl:running"
LOCK_TTL_SECONDS = 30 * 60

MAX_PAGES = 20
MAX_DETAIL = 500

_memory_status: dict = {}

# Giữ tham chiếu tới task đang chạy: `asyncio.create_task` chỉ giữ tham
# chiếu YẾU, task không được ai giữ có thể bị thu gom giữa chừng và mẻ ETL
# im lặng biến mất.
_running_tasks: set[asyncio.Task] = set()


async def _set_status(status: dict) -> None:
    global _memory_status
    _memory_status = status
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.setex(STATUS_KEY, STATUS_TTL_SECONDS, json.dumps(status, ensure_ascii=False))
    except Exception:
        logger.exception("Không ghi được trạng thái ETL vào Redis")


async def _get_status() -> dict:
    redis = get_redis()
    if redis is not None:
        try:
            raw = await redis.get(STATUS_KEY)
            if raw:
                return json.loads(raw)
        except Exception:
            logger.exception("Không đọc được trạng thái ETL từ Redis")
    return _memory_status


async def _acquire_lock() -> bool:
    redis = get_redis()
    if redis is None:
        return _memory_status.get("state") != "running"
    try:
        return bool(await redis.set(LOCK_KEY, "1", ex=LOCK_TTL_SECONDS, nx=True))
    except Exception:
        logger.exception("Không lấy được khoá ETL")
        return True


async def _release_lock() -> None:
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.delete(LOCK_KEY)
    except Exception:
        logger.exception("Không nhả được khoá ETL")


async def _run_in_background(sources: list[str] | None, pages: int, detail: int) -> None:
    await _set_status({"state": "running", "startedAt": utc_now().isoformat(), "sources": sources or list(SOURCES)})
    try:
        report = await run_etl(sources=sources, pages=pages, detail_limit=detail)
        await _set_status({"state": "done", **report.to_dict()})
    except Exception as err:
        logger.exception("ETL nền hỏng")
        await _set_status(
            {"state": "failed", "error": f"{type(err).__name__}: {err}", "finishedAt": utc_now().isoformat()}
        )
    finally:
        await _release_lock()


async def start_etl(decoded_user: dict, sources: list[str] | None, pages: int, detail: int):
    require_admin(decoded_user)

    unknown = [s for s in (sources or []) if s not in SOURCES]
    if unknown:
        raise ApiError(400, code="admin.unknownSource", params={"sources": ", ".join(unknown)})
    if not 1 <= pages <= MAX_PAGES:
        raise ApiError(400, code="admin.pagesOutOfRange", params={"max": MAX_PAGES})
    if not 0 <= detail <= MAX_DETAIL:
        raise ApiError(400, code="admin.detailOutOfRange", params={"max": MAX_DETAIL})

    if not await _acquire_lock():
        raise ApiError(409, code="admin.etlRunning")

    # `create_task` chứ không `await`: response trả ngay, tác vụ chạy tiếp.
    task = asyncio.create_task(_run_in_background(sources, pages, detail))
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)
    return ok(code="admin.etlStarted")


async def etl_status(decoded_user: dict):
    require_admin(decoded_user)
    return ok(
        status=await _get_status() or {"state": "idle"},
        stats={
            "jobs": await Job.find({"is_active": True}).count(),
            "companies": await Company.find_all().count(),
            "jobsWithVector": await Job.find({"embedding": {"$ne": None}}).count(),
            "companiesWithProfile": await Company.find({"description": {"$ne": ""}}).count(),
        },
        sources=sorted(SOURCES),
    )
