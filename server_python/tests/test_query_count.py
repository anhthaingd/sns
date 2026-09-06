"""Đếm số lệnh gửi xuống MongoDB cho mỗi endpoint — chốt chặn chống N+1.

Cách đo: nạp CHÍNH app FastAPI vào tiến trình test (`httpx.ASGITransport`) và
gắn một `pymongo.monitoring.CommandListener` để đếm lệnh đọc. Đo trong tiến
trình thay vì qua HTTP vì listener chỉ thấy được lệnh của client trong cùng
tiến trình.

Số đo TRƯỚC khi có `app/utils/loaders.py` (bằng Mongo profiler, dữ liệu thật):

    GET /api/posts?page=1                          53 lệnh
    GET /api/channels?page=1 (1 channel, 11 người) 64 lệnh

Ngưỡng ở đây cố ý đặt sát để nếu ai đó vô tình đưa `await Model.get()` trở lại
vào vòng lặp thì test đỏ ngay.
"""

import uuid

import pymongo.monitoring
import pytest
import pytest_asyncio

READ_COMMANDS = {"find", "aggregate", "count", "getMore", "distinct"}


class _ReadCounter(pymongo.monitoring.CommandListener):
    def __init__(self):
        self.recording = False
        self.commands: list[str] = []

    def started(self, event):
        if self.recording and event.command_name in READ_COMMANDS:
            self.commands.append(event.command_name)

    def succeeded(self, event):
        pass

    def failed(self, event):
        pass


# Listener phải đăng ký TRƯỚC khi tạo MongoClient, nên đặt ở cấp module.
_counter = _ReadCounter()
pymongo.monitoring.register(_counter)


@pytest_asyncio.fixture  # function-scope: fixture async scope module se lech event loop voi pytest-asyncio
async def inprocess_app():
    import httpx
    from app.config.database import close_db, connect_db
    from app.main import app

    await connect_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://inprocess", timeout=60.0) as c:
        yield c
    await close_db()


class _Recording:
    def __init__(self, counter):
        self._counter = counter

    def __enter__(self):
        self._counter.commands.clear()
        self._counter.recording = True
        return self._counter

    def __exit__(self, *_):
        self._counter.recording = False


@pytest.fixture
def count_reads():
    return lambda: _Recording(_counter)


async def _seed_posts(client, admin, channel, user, how_many=6):
    """Bài viết có tác giả + bình luận + like để có quan hệ mà populate."""
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)
    for i in range(how_many):
        r = await client.post(
            f"/api/posts/{channel['_id']}",
            headers=user.headers,
            data={"content": f"query-count-{uuid.uuid4().hex[:6]}-{i}"},
        )
        assert r.status_code == 201, r.text

    r = await client.get(f"/api/posts/{channel['_id']}", headers=user.headers)
    for post in r.json()["posts"][:how_many]:
        await client.post(
            f"/api/posts/{channel['_id']}/{post['_id']}/comments",
            headers=user.headers,
            json={"content": "cmt"},
        )
        await client.post(f"/api/posts/{channel['_id']}/{post['_id']}/like_post", headers=admin.headers)


async def test_get_posts_does_not_scale_with_page_size(client, inprocess_app, count_reads, user, admin, channel):
    await _seed_posts(client, admin, channel, user)

    with count_reads() as counter:
        r = await inprocess_app.get("/api/posts?page=1", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["posts"], "cần có bài viết thì phép đo mới có ý nghĩa"

    total = len(counter.commands)
    # Chặn dưới: nếu listener hỏng thì total = 0 và test sẽ xanh giả.
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 8, f"GET /api/posts dùng {total} lệnh đọc (trước tối ưu: 53) — N+1 quay lại?"


async def test_get_channels_does_not_scale_with_member_count(client, inprocess_app, count_reads, user, admin, channel):
    await client.post(f"/api/channels/{channel['_id']}", headers=user.headers)

    with count_reads() as counter:
        r = await inprocess_app.get("/api/channels?page=1", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["channels"]

    total = len(counter.commands)
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 6, f"GET /api/channels dùng {total} lệnh đọc (trước tối ưu: 64) — N+1 quay lại?"


async def test_get_newest_messages_is_batched(client, inprocess_app, count_reads, user):
    with count_reads() as counter:
        r = await inprocess_app.get("/api/newest_messages", headers=user.headers)
    assert r.status_code == 200, r.text

    total = len(counter.commands)
    assert total >= 1, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 5, f"GET /api/newest_messages dùng {total} lệnh đọc"


async def test_job_list_does_not_scale_with_page_size(client, inprocess_app, count_reads, user, has_jobs):
    """`GET /api/jobs` phải nạp công ty theo lô, không phải `Company.get()` mỗi tin."""
    with count_reads() as counter:
        r = await inprocess_app.get("/api/jobs?page=1", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["jobs"]

    total = len(counter.commands)
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 5, f"GET /api/jobs dùng {total} lệnh đọc — N+1 quay lại?"


async def test_match_companies_scores_hundreds_of_jobs_with_few_queries(
    client, inprocess_app, count_reads, user_with_resume, has_jobs
):
    """Chấm hàng trăm tin phải tốn rất ít truy vấn.

    Độ tương đồng lấy từ chỉ mục vector trong bộ nhớ, phần chấm điểm là logic
    thuần — nên số truy vấn KHÔNG được tăng theo số tin. Nếu chỗ này phình lên
    thì nghĩa là ai đó đã đưa truy vấn vào vòng lặp chấm điểm.
    """
    with count_reads() as counter:
        r = await inprocess_app.get("/api/match/companies?page=1", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["matches"]

    total = len(counter.commands)
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 6, f"GET /api/match/companies dùng {total} lệnh đọc để chấm {body['totalCompanies']} công ty"


async def test_whatif_scores_every_job_many_times_with_few_queries(
    client, inprocess_app, count_reads, user_with_resume, has_jobs
):
    """Mô phỏng chấm 430 tin × 13 phương án nhưng chỉ được đọc DB đúng vài lần.

    Đây là chỗ dễ hỏng nhất về hiệu năng: chỉ cần một `Company.get()` hay
    `Job.get()` lọt vào vòng lặp chấm điểm là thành hàng nghìn truy vấn mà
    trang vẫn chạy đúng, chỉ chậm dần cho tới khi không mở nổi.
    """
    with count_reads() as counter:
        r = await inprocess_app.get("/api/match/whatif", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    assert r.json()["suggestions"]

    total = len(counter.commands)
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 5, f"GET /api/match/whatif dùng {total} lệnh đọc — có truy vấn lọt vào vòng lặp?"


async def test_market_aggregates_in_a_fixed_number_of_queries(client, inprocess_app, count_reads, user, has_jobs):
    """Thống kê phải gộp bằng aggregation, không phải đếm từng kỹ năng một."""
    with count_reads() as counter:
        r = await inprocess_app.get("/api/jobs/market", headers=user.headers)
    assert r.status_code == 200, r.text
    assert r.json()["skills"]

    total = len(counter.commands)
    assert total >= 2, "listener không ghi được lệnh nào — phép đo không đáng tin"
    assert total <= 8, f"GET /api/jobs/market dùng {total} lệnh đọc — đếm từng nhóm một?"
