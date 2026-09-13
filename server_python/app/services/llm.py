"""Gọi mô hình ngôn ngữ qua giao thức tương thích OpenAI.

Module này **không biết gì về CV hay tin tuyển dụng**. Nó nhận `messages` cùng
một JSON Schema rồi trả về dict đã parse, hoặc `None`. Mọi hiểu biết nghiệp vụ
nằm ở `app/services/llm_advice.py`.

Nguyên tắc giống hệt `app/services/embedding.py`: **hỏng thì trả `None`, không
bao giờ ném ra ngoài.** Lời khuyên là phần làm màn hình hay hơn, không phải
phần bắt buộc — mất nó thì giao diện ẩn một cái thẻ, chứ không hiện màn hình
lỗi nào.

Đo ngày 13/09/2026 trên gói miễn phí của cả hai bên: gọi `gemini-flash-latest`
ba lần thì lần thứ hai dính 429, và `gemini-3.8-flash` trả 503 cả 8/8 lần với
payload thật. **429/503 rải rác là trạng thái bình thường ở gói miễn phí, không
phải sự cố** — nên chuỗi dự phòng và cầu dao dưới đây là phần bắt buộc.
"""

import json
import logging
import time
from dataclasses import dataclass

import httpx

from app.config.redis_client import get_redis
from app.config.settings import (
    LLM_BREAKER_COOLDOWN_SECONDS,
    LLM_BREAKER_THRESHOLD,
    LLM_ENABLED,
    LLM_FALLBACK_API_KEY,
    LLM_FALLBACK_BASE_URL,
    LLM_FALLBACK_MODEL,
    LLM_MAX_TOKENS,
    LLM_PRIMARY_API_KEY,
    LLM_PRIMARY_BASE_URL,
    LLM_PRIMARY_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
)

logger = logging.getLogger("fuurin.llm")


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    api_key: str


def providers() -> list[Provider]:
    """Danh sách nhà cung cấp còn dùng được, theo thứ tự ưu tiên.

    Đọc cấu hình mỗi lần gọi chứ không dựng sẵn lúc import, để test
    `monkeypatch` được và để đổi biến môi trường không phải restart tiến trình.
    """
    if not LLM_ENABLED:
        return []
    candidates = [
        Provider("primary", LLM_PRIMARY_BASE_URL, LLM_PRIMARY_MODEL, LLM_PRIMARY_API_KEY),
        Provider("fallback", LLM_FALLBACK_BASE_URL, LLM_FALLBACK_MODEL, LLM_FALLBACK_API_KEY),
    ]
    return [p for p in candidates if p.api_key and p.base_url and p.model]


def is_configured() -> bool:
    return bool(providers())


# --- Cầu dao ---------------------------------------------------------------
# Redis chứ không phải biến trong tiến trình: mọi worker phải cùng biết một nhà
# cung cấp đang hỏng, nếu không thì worker thứ hai lại đâm đầu vào đúng chỗ đó.
# Không có Redis thì đếm tạm trong bộ nhớ — cùng cách xử lý với rate_limit.py.
_memory_breaker: dict[str, tuple[int, float]] = {}


def _breaker_key(provider: Provider) -> str:
    return f"llm:breaker:{provider.name}:{provider.model}"


async def _is_open(provider: Provider) -> bool:
    """Cầu dao đang ngắt -> bỏ qua nhà cung cấp này."""
    key = _breaker_key(provider)
    redis = get_redis()
    if redis is None:
        fails, until = _memory_breaker.get(key, (0, 0.0))
        return fails >= LLM_BREAKER_THRESHOLD and time.time() < until
    try:
        return int(await redis.get(key) or 0) >= LLM_BREAKER_THRESHOLD
    except Exception:
        logger.exception("Cầu dao không đọc được Redis, coi như đang đóng")
        return False


async def _record_failure(provider: Provider) -> None:
    key = _breaker_key(provider)
    redis = get_redis()
    if redis is None:
        fails, _ = _memory_breaker.get(key, (0, 0.0))
        _memory_breaker[key] = (fails + 1, time.time() + LLM_BREAKER_COOLDOWN_SECONDS)
        return
    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        # nx=True: đặt hạn ở lần hỏng đầu tiên -> cửa sổ cố định. Không có nó
        # thì mỗi lần hỏng lại gia hạn, cầu dao ngắt vĩnh viễn.
        pipe.expire(key, LLM_BREAKER_COOLDOWN_SECONDS, nx=True)
        await pipe.execute()
    except Exception:
        logger.exception("Cầu dao không ghi được Redis")


async def _record_success(provider: Provider) -> None:
    key = _breaker_key(provider)
    _memory_breaker.pop(key, None)
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.delete(key)
    except Exception:
        logger.exception("Cầu dao không xoá được bộ đếm")


# --- Gọi -------------------------------------------------------------------
_clients: dict[str, httpx.AsyncClient] = {}


def _client(provider: Provider) -> httpx.AsyncClient:
    if provider.base_url not in _clients:
        _clients[provider.base_url] = httpx.AsyncClient(
            base_url=provider.base_url,
            timeout=LLM_TIMEOUT_SECONDS,
        )
    return _clients[provider.base_url]


async def close_llm() -> None:
    for client in list(_clients.values()):
        await client.aclose()
    _clients.clear()


def _body(provider: Provider, messages: list[dict], schema: dict, schema_name: str) -> dict:
    return {
        "model": provider.model,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "messages": messages,
        # Đo được: cả hai nhà cung cấp đều nhận `json_schema`. Tầng kiểm bằng
        # Pydantic ở llm_advice.py vẫn giữ — nó còn bắt được cả JSON bị cắt
        # ngang vì hết max_tokens, thứ đã thật sự xảy ra lúc đo.
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    }


async def _ask(provider: Provider, messages: list[dict], schema: dict, schema_name: str) -> dict | None:
    try:
        response = await _client(provider).post(
            "/chat/completions",
            json=_body(provider, messages, schema, schema_name),
            headers={"Authorization": f"Bearer {provider.api_key}"},
        )
    except Exception as err:
        logger.warning("LLM %s (%s) không gọi được: %s", provider.name, provider.model, err)
        return None

    if response.status_code != 200:
        # 429/503 là chuyện thường ở gói miễn phí -> warning, không phải error.
        logger.warning(
            "LLM %s (%s) trả %s: %s",
            provider.name,
            provider.model,
            response.status_code,
            response.text[:200].replace("\n", " "),
        )
        return None

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except Exception:
        logger.warning("LLM %s trả về thân response lạ", provider.name)
        return None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Gần như luôn là JSON bị cắt vì hết max_tokens, không phải model bịa.
        logger.warning("LLM %s trả JSON không parse được (có thể bị cắt vì max_tokens)", provider.name)
        return None

    return parsed if isinstance(parsed, dict) else None


async def complete_json(messages: list[dict], schema: dict, schema_name: str = "advice") -> dict | None:
    """Hỏi lần lượt từng nhà cung cấp, trả dict đầu tiên đọc được — hoặc `None`.

    Không thử lại trong cùng một nhà cung cấp: khi bên chính trả 429/503 thì
    chờ nó hồi phục vô nghĩa, sang thẳng bên dự phòng vừa nhanh hơn vừa đỡ tốn
    hạn mức. Đo được: bên dự phòng trả lời trong 0.8 giây.
    """
    for provider in providers():
        if await _is_open(provider):
            logger.info("LLM %s đang bị cầu dao ngắt, bỏ qua", provider.name)
            continue

        started = time.monotonic()
        result = await _ask(provider, messages, schema, schema_name)
        elapsed = time.monotonic() - started

        if result is None:
            await _record_failure(provider)
            continue

        await _record_success(provider)
        logger.info("LLM %s (%s) trả lời trong %.1fs", provider.name, provider.model, elapsed)
        return result

    return None
