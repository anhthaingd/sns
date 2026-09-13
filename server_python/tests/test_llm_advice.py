"""Tầng dựng lời khuyên — kiểm phần làm sạch đầu ra và các nhánh từ chối.

Không chạm mạng và không cần API key: mọi lời gọi nhà cung cấp đều bị thay bằng
hàm giả.
"""

import app.services.llm as llm
import app.services.llm_advice as advice_module
import pytest
from app.services.llm_advice import MAX_MONTHS, MAX_SUMMARY, _trim, _validated, advise

GOOD = {
    "summary": "Câu một. Câu hai. Câu ba.",
    "roadmap": [{"title": "Học N2", "detail": "Ôn đều mỗi ngày", "months": 6}],
}


@pytest.fixture(autouse=True)
def no_provider_by_default(monkeypatch):
    monkeypatch.setattr(llm, "LLM_ENABLED", True)
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "")
    monkeypatch.setattr(llm, "LLM_FALLBACK_API_KEY", "")


# --- Cắt chuỗi --------------------------------------------------------------


def test_short_text_is_returned_untouched():
    assert _trim("Một câu ngắn.", MAX_SUMMARY) == "Một câu ngắn."


def test_long_text_is_cut_at_a_sentence_boundary_not_mid_word():
    """Bản đầu cắt cứng theo ký tự và để lại "...phỏng vấn ng" — trông như lỗi
    hiển thị chứ không như lời khuyên."""
    text = "Câu đầu tiên đủ dài để giữ lại. " + "x" * 200
    out = _trim(text, 60)
    assert out == "Câu đầu tiên đủ dài để giữ lại."
    assert not out.endswith("x")


def test_japanese_sentence_mark_is_understood():
    """Tiếng Nhật kết câu bằng 。 chứ không phải dấu chấm."""
    text = "日本語のレベルを上げてください。" + "あ" * 200
    out = _trim(text, 40)
    assert out == "日本語のレベルを上げてください。"


def test_falls_back_to_word_boundary_when_there_is_no_sentence_end():
    out = _trim("mot cau rat dai khong he co dau cham nao ca nen phai cat theo tu", 30)
    assert out.endswith("…")
    assert " " not in out[-2:]


# --- Kiểm khuôn đầu ra ------------------------------------------------------


def test_rejects_output_with_wrong_shape():
    assert _validated({"summary": "thiếu roadmap"}) is None
    assert _validated({"roadmap": []}) is None
    assert _validated(None) is None


def test_clamps_months_instead_of_rejecting():
    """ "36 tháng" vẫn là lời khuyên dùng được, chỉ cần kéo về thang vẽ được."""
    out = _validated({"summary": "ok", "roadmap": [{"title": "t", "detail": "d", "months": 99}]})
    assert out["roadmap"][0]["months"] == MAX_MONTHS


def test_strips_urls_from_the_output():
    """Không kiểm chứng được liên kết dẫn tới đâu thì không hiện liên kết nào."""
    out = _validated(
        {
            "summary": "Xem tại https://example.com/khoa-hoc để biết thêm.",
            "roadmap": [{"title": "t", "detail": "vào www.example.com", "months": 3}],
        }
    )
    assert "example.com" not in out["summary"]
    assert "example.com" not in out["roadmap"][0]["detail"]


# --- Các nhánh từ chối ------------------------------------------------------


async def test_returns_disabled_when_no_provider_is_configured():
    result, reason = await advise("job", "vi", {"gaps": []}, "user-1")
    assert result is None
    assert reason == "disabled"


async def test_returns_unavailable_when_every_provider_fails(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "key")
    monkeypatch.setattr(advice_module.llm, "complete_json", _async_return(None))

    result, reason = await advise("job", "vi", {"gaps": []}, "user-1")
    assert result is None
    assert reason == "unavailable"


async def test_returns_quota_when_the_user_runs_out_of_budget(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "key")
    monkeypatch.setattr(advice_module, "LLM_USER_RATE_LIMIT_MAX", 0)
    called = []
    monkeypatch.setattr(advice_module.llm, "complete_json", _async_return(GOOD, called))

    result, reason = await advise("job", "vi", {"gaps": []}, "user-quota")
    assert (result, reason) == (None, "quota")
    # Quan trọng: chạm trần thì KHÔNG gọi nhà cung cấp nữa.
    assert called == []


async def test_happy_path_returns_cleaned_advice(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PRIMARY_API_KEY", "key")
    monkeypatch.setattr(advice_module.llm, "complete_json", _async_return(GOOD))

    result, reason = await advise("market", "ja", {"totalJobs": 430}, "user-2")
    assert reason == "ok"
    assert result["summary"].startswith("Câu một")
    assert result["roadmap"][0]["months"] == 6


async def test_unknown_kind_is_a_programming_error_not_a_silent_pass():
    with pytest.raises(ValueError):
        await advise("khong-ton-tai", "vi", {}, "user-3")


def _async_return(value, log=None):
    async def fake(*args, **kwargs):
        if log is not None:
            log.append(args)
        return value

    return fake
