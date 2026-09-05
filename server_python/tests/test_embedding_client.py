"""Client gọi service embedder — kiểm phần suy giảm êm.

Nguyên tắc: embedder hỏng thì trả `None`, KHÔNG ném lỗi. Tầng gọi dựa vào đó để
chuyển sang chấm điểm thuần luật.
"""

import app.services.embedding as embedding_module
from app.services.embedding import embed_texts, is_available


async def test_returns_none_when_embedder_url_is_not_configured(monkeypatch):
    monkeypatch.setattr(embedding_module, "EMBEDDER_URL", "")
    monkeypatch.setattr(embedding_module, "_client", None)

    assert await embed_texts(["xin chào"]) is None
    assert await is_available() is False


async def test_returns_none_when_embedder_is_unreachable(monkeypatch):
    """Cổng không ai nghe -> coi như không có, không được ném ra ngoài."""
    monkeypatch.setattr(embedding_module, "EMBEDDER_URL", "http://127.0.0.1:9")
    monkeypatch.setattr(embedding_module, "_client", None)
    monkeypatch.setattr(embedding_module, "EMBEDDER_TIMEOUT_SECONDS", 2)

    assert await embed_texts(["xin chào"]) is None
    assert await is_available() is False

    await embedding_module.close_embedder()


async def test_empty_input_returns_empty_list_without_calling_the_service(monkeypatch):
    monkeypatch.setattr(embedding_module, "EMBEDDER_URL", "http://127.0.0.1:9")
    assert await embed_texts([]) == []
