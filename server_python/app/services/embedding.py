"""Gọi service embedder để lấy vector ngữ nghĩa.

Nguyên tắc: **embedder chết thì hệ thống vẫn chạy.** Xếp hạng theo ngữ nghĩa là
phần làm kết quả đẹp hơn, không phải phần bắt buộc — tầng lọc theo luật (JLPT,
số năm, lương, địa điểm) vẫn cho ra danh sách công ty phù hợp mà không cần
vector nào. Vì vậy mọi lỗi ở đây đều trả `None` chứ không ném ra ngoài; tầng
gọi tự chuyển sang chấm điểm thuần luật.
"""

import logging

import httpx

from app.config.settings import EMBEDDER_TIMEOUT_SECONDS, EMBEDDER_URL

logger = logging.getLogger("fuurin.embedding")

# Model nhận vài trăm token đầu; gửi nhiều hơn chỉ tốn băng thông.
MAX_CHARS = 4000
# Service chặn ở 256 text mỗi request.
BATCH_SIZE = 128

_client: httpx.AsyncClient | None = None
# Số chiều và tên model do service quyết định — ghi lại để biết vector nào đã
# lỗi thời khi đổi model.
_model_name: str | None = None


def get_model_name() -> str | None:
    return _model_name


async def close_embedder() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _get_client() -> httpx.AsyncClient | None:
    global _client
    if not EMBEDDER_URL:
        return None
    if _client is None:
        _client = httpx.AsyncClient(base_url=EMBEDDER_URL, timeout=EMBEDDER_TIMEOUT_SECONDS)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Vector cho từng đoạn văn bản, cùng thứ tự. Trả `None` nếu không dùng được."""
    global _model_name

    if not texts:
        return []

    client = _get_client()
    if client is None:
        return None

    vectors: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = [(t or " ")[:MAX_CHARS] for t in texts[start : start + BATCH_SIZE]]
        try:
            response = await client.post("/embed", json={"texts": batch})
            response.raise_for_status()
        except Exception as err:
            logger.warning("Không gọi được embedder (%s) — chuyển sang chấm điểm thuần luật: %s", EMBEDDER_URL, err)
            return None
        payload = response.json()
        _model_name = payload.get("model")
        vectors.extend(payload["vectors"])

    return vectors


async def embed_one(text: str) -> list[float] | None:
    vectors = await embed_texts([text])
    return vectors[0] if vectors else None


async def is_available() -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        response = await client.get("/health")
        return response.status_code == 200 and response.json().get("status") == "ok"
    except Exception:
        return False
