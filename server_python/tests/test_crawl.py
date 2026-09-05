"""Crawl phụ thuộc mạng ngoài -> chỉ chạy khi bật RUN_CRAWL_TESTS=1."""

import os

import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_CRAWL_TESTS") != "1", reason="cần internet, bật bằng RUN_CRAWL_TESTS=1")


@pytest.mark.parametrize("path", ["/crawl/dai_job", "/crawl/gaijinpot", "/crawl/nihongo", "/crawl/linked_jp_jobs"])
async def test_crawl_returns_html(client, path):
    r = await client.get(path, params={"curPage": 1}, timeout=180)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["html"], list)
    assert len(body["html"]) > 0, f"{path} trả về 0 job — selector có thể đã lỗi thời"
