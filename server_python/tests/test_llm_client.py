"""Tầng gọi LLM — kiểm phần suy giảm êm và chuyển nhà cung cấp.

Không chạm mạng: mọi lời gọi đi qua `httpx.MockTransport`. CI không có API key
và sẽ không bao giờ có, nên toàn bộ hành vi quan trọng phải kiểm được offline.

Nguyên tắc bị khoá ở đây: **hỏng thì trả `None`, không ném lỗi.** Tầng gọi dựa
vào đó để ẩn thẻ gợi ý thay vì hiện màn hình lỗi.
"""

import json

import app.services.llm as llm
import httpx
import pytest

SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}
MESSAGES = [{"role": "user", "content": "xin chào"}]


def _answer(payload: dict) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(payload)}}]})


@pytest.fixture(autouse=True)
def two_providers(monkeypatch):
    """Cấu hình hai nhà cung cấp giả và xoá trạng thái cầu dao giữa các test."""
    monkeypatch.setattr(llm, "LLM_ENABLED", True)
    monkeypatch.setattr(llm, "LLM_PRIMARY_BASE_URL", "https://primary.test/v1")
    monkeypatch.setattr(llm, "LLM_PRIMARY_MODEL", "model-chinh")
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "key-chinh")
    monkeypatch.setattr(llm, "LLM_FALLBACK_BASE_URL", "https://fallback.test/v1")
    monkeypatch.setattr(llm, "LLM_FALLBACK_MODEL", "model-du-phong")
    monkeypatch.setattr(llm, "LLM_FALLBACK_API_KEY", "key-du-phong")
    llm._memory_breaker.clear()
    yield
    llm._memory_breaker.clear()


def route(monkeypatch, handlers: dict):
    """Gắn mỗi nhà cung cấp với một hàm trả lời, và đếm số lần bị gọi."""
    calls: list[str] = []

    def make(name):
        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(name)
            return handlers[name](request)

        return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://x.test")

    clients = {"primary": make("primary"), "fallback": make("fallback")}
    monkeypatch.setattr(llm, "_client", lambda provider: clients[provider.name])
    return calls


async def test_returns_none_when_no_api_key_is_configured(monkeypatch):
    """Không cấu hình key -> tính năng tắt, và KHÔNG gọi đi đâu cả."""
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "")
    monkeypatch.setattr(llm, "LLM_FALLBACK_API_KEY", "")
    calls = route(monkeypatch, {})

    assert llm.is_configured() is False
    assert await llm.complete_json(MESSAGES, SCHEMA) is None
    assert calls == []


async def test_returns_none_when_disabled_by_flag(monkeypatch):
    monkeypatch.setattr(llm, "LLM_ENABLED", False)
    calls = route(monkeypatch, {})

    assert await llm.complete_json(MESSAGES, SCHEMA) is None
    assert calls == []


async def test_uses_primary_when_it_answers(monkeypatch):
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: _answer({"summary": "từ bên chính"}),
            "fallback": lambda r: _answer({"summary": "không nên chạm tới"}),
        },
    )

    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "từ bên chính"}
    assert calls == ["primary"]


async def test_falls_back_to_second_provider_on_429(monkeypatch):
    """429 ở gói miễn phí là chuyện thường — phải sang bên dự phòng, không được hỏng."""
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: httpx.Response(429, text="rate limited"),
            "fallback": lambda r: _answer({"summary": "từ bên dự phòng"}),
        },
    )

    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "từ bên dự phòng"}
    assert calls == ["primary", "fallback"]


async def test_falls_back_on_503(monkeypatch):
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: httpx.Response(503, text="high demand"),
            "fallback": lambda r: _answer({"summary": "vẫn chạy"}),
        },
    )

    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "vẫn chạy"}
    assert calls == ["primary", "fallback"]


async def test_falls_back_when_json_is_truncated(monkeypatch):
    """JSON bị cắt vì hết max_tokens — đã xảy ra thật lúc đo, không phải giả định."""
    cut = httpx.Response(200, json={"choices": [{"message": {"content": '{"summary": "câu bị cắt ngang'}}]})
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: cut,
            "fallback": lambda r: _answer({"summary": "nguyên vẹn"}),
        },
    )

    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "nguyên vẹn"}
    assert calls == ["primary", "fallback"]


async def test_falls_back_when_provider_times_out(monkeypatch):
    def boom(request):
        raise httpx.ReadTimeout("quá giờ", request=request)

    calls = route(monkeypatch, {"primary": boom, "fallback": lambda r: _answer({"summary": "kịp"})})

    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "kịp"}
    assert calls == ["primary", "fallback"]


async def test_returns_none_when_both_providers_fail(monkeypatch):
    """Cả hai hỏng -> `None`. Tầng gọi ẩn thẻ gợi ý, KHÔNG có màn hình lỗi."""
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: httpx.Response(500, text="lỗi"),
            "fallback": lambda r: httpx.Response(500, text="lỗi"),
        },
    )

    assert await llm.complete_json(MESSAGES, SCHEMA) is None
    assert calls == ["primary", "fallback"]


async def test_breaker_stops_calling_a_provider_that_keeps_failing(monkeypatch):
    """Hết hạn mức ngày kéo dài hàng giờ.

    Không có cầu dao thì mọi request sau đó vẫn phải chờ hết timeout rồi mới bỏ
    cuộc — người dùng chịu thêm 12 giây chờ để nhận về đúng thứ họ sẽ nhận nếu
    không gọi gì cả.
    """
    monkeypatch.setattr(llm, "LLM_BREAKER_THRESHOLD", 2)
    calls = route(
        monkeypatch,
        {
            "primary": lambda r: httpx.Response(429, text="hết hạn mức"),
            "fallback": lambda r: _answer({"summary": "vẫn chạy"}),
        },
    )

    for _ in range(2):
        assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "vẫn chạy"}
    assert calls.count("primary") == 2

    # Chạm ngưỡng -> lần sau không gọi bên chính nữa, đi thẳng bên dự phòng.
    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "vẫn chạy"}
    assert calls.count("primary") == 2
    assert calls.count("fallback") == 3


async def test_success_resets_the_breaker(monkeypatch):
    monkeypatch.setattr(llm, "LLM_BREAKER_THRESHOLD", 2)
    state = {"fail": True}

    def flaky(request):
        return httpx.Response(503, text="quá tải") if state["fail"] else _answer({"summary": "ok"})

    route(monkeypatch, {"primary": flaky, "fallback": lambda r: _answer({"summary": "dự phòng"})})

    await llm.complete_json(MESSAGES, SCHEMA)
    state["fail"] = False
    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "ok"}

    # Một lần thành công xoá sạch bộ đếm, không để lại "nợ" cho lần hỏng sau.
    state["fail"] = True
    await llm.complete_json(MESSAGES, SCHEMA)
    state["fail"] = False
    assert await llm.complete_json(MESSAGES, SCHEMA) == {"summary": "ok"}
