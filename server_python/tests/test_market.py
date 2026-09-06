"""Test tầng thống kê thị trường.

Hai thứ được canh ở đây, và cả hai đều là chuyện TRUNG THỰC chứ không phải
chuyện code chạy đúng:

  * mọi trung vị phải kèm cỡ mẫu — đo trên dữ liệu thật, nhóm tin yêu cầu tiếng
    Nhật mức `none` chỉ có 12 tin ghi lương, mức `fluent` có 12 tin; đặt cạnh
    một trung vị tính trên 101 tin mà không nói cỡ mẫu là đánh lừa người đọc;
  * nhóm quá nhỏ không được đứng riêng như thể nó là một quy luật.
"""

from app.services.market import MIN_GROUP_SIZE, median


def test_median_ignores_missing_values():
    assert median([None, 100, None, 300, 200]) == 200


def test_median_returns_none_when_nothing_is_known():
    assert median([None, None]) is None
    assert median([]) is None


async def test_market_requires_authentication(client):
    assert (await client.get("/api/jobs/market")).status_code == 401


async def test_market_reports_skill_demand(client, user, has_jobs):
    r = await client.get("/api/jobs/market", headers=user.headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["totalJobs"] > 0
    assert body["skills"], "không có kỹ năng nào — dữ liệu ETL trống?"

    # `__other__` là PHẦN DƯ gộp từ hàng chục kỹ năng lẻ, không phải một kỹ
    # năng — tổng của nó lớn hơn kỹ năng đứng đầu là chuyện bình thường (đo
    # được: 200 so với 109). Nên nó luôn đứng cuối và không tham gia xếp hạng.
    named = [s for s in body["skills"] if s["skill"] != "__other__"]
    counts = [s["jobs"] for s in named]
    assert counts == sorted(counts, reverse=True), "kỹ năng có tên phải xếp giảm dần theo số tin"
    if len(named) < len(body["skills"]):
        assert body["skills"][-1]["skill"] == "__other__", "phần dư phải nằm cuối danh sách"


async def test_every_median_comes_with_its_sample_size(client, user, has_jobs):
    """Trung vị không kèm cỡ mẫu là trưng nhiễu như thể là quy luật."""
    body = (await client.get("/api/jobs/market", headers=user.headers)).json()
    for group in ("skills", "japanese", "prefectures"):
        for row in body[group]:
            assert "salarySample" in row, f"{group}: thiếu cỡ mẫu"
            if row["salaryMedian"] is not None:
                assert row["salarySample"] >= MIN_GROUP_SIZE, (
                    f"{group}/{row}: trung vị tính trên {row['salarySample']} tin thì không nói lên gì"
                )


async def test_small_skill_groups_are_merged_instead_of_listed(client, user, has_jobs):
    body = (await client.get("/api/jobs/market", headers=user.headers)).json()
    named = [s for s in body["skills"] if s["skill"] != "__other__"]
    assert all(s["jobs"] >= MIN_GROUP_SIZE for s in named), "nhóm nhỏ phải được gộp vào __other__"
