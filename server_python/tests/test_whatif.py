"""Test engine mô phỏng đối chứng — dựng CV và tin bằng tay, không cần DB.

Test quan trọng nhất trong file này là `test_deltas_do_not_add_up`: nó pin lại
đúng cái tính chất khiến chức năng này phải tồn tại dưới dạng một engine chấm
lại, chứ không phải một bảng tra sẵn.
"""

import pytest
from app.models.job import JobMatchView
from app.models.resume import ResumeMatchView
from app.services.whatif import (
    MAX_SIMULATED_YEARS,
    Action,
    apply_actions,
    candidate_actions,
    qualified_job_ids,
    simulate,
)
from bson import ObjectId


def make_job(**kwargs) -> JobMatchView:
    defaults = {"_id": ObjectId(), "url": "https://example.com/1", "title": "Engineer"}
    return JobMatchView(**{**defaults, **kwargs})


def make_resume(**kwargs) -> ResumeMatchView:
    return ResumeMatchView(**kwargs)


# ---------------------------------------------------------------------------
# Áp dụng phương án
# ---------------------------------------------------------------------------


def test_applying_a_skill_does_not_mutate_the_original_resume():
    """Nhân bản chứ không sửa tại chỗ — nếu không, lượt mô phỏng thứ hai sẽ
    chấm trên một CV đã bị lượt trước làm bẩn."""
    resume = make_resume(skills_normalized=["Python"])
    after = apply_actions(resume, [Action(kind="skill", value="AWS")])

    assert resume.skills_normalized == ["Python"]
    assert set(after.skills_normalized) == {"Python", "AWS"}


def test_applying_a_japanese_level_replaces_it():
    resume = make_resume(japanese_level="basic")
    after = apply_actions(resume, [Action(kind="japanese", value="business")])
    assert after.japanese_level == "business"
    assert resume.japanese_level == "basic"


def test_applying_two_language_levels_keeps_the_higher_one():
    """Tick cả N2 lẫn N1 thì kết quả phải là N1, và KHÔNG phụ thuộc thứ tự gửi lên.

    Bản đầu ghi đè tuần tự nên cùng một lựa chọn của người dùng cho hai kết quả
    khác nhau tuỳ thứ tự phần tử trong mảng (đo được: +68 so với +64).
    """
    resume = make_resume(japanese_level="basic")
    up = [Action("japanese", "business"), Action("japanese", "fluent")]

    assert apply_actions(resume, up).japanese_level == "fluent"
    assert apply_actions(resume, list(reversed(up))).japanese_level == "fluent"


def test_applying_a_lower_level_never_downgrades_the_resume():
    """Mô phỏng là "nếu tôi HỌC THÊM"; không có phương án nào làm CV kém đi."""
    resume = make_resume(japanese_level="fluent", english_level="business")
    after = apply_actions(resume, [Action("japanese", "basic"), Action("english", "none")])
    assert after.japanese_level == "fluent"
    assert after.english_level == "business"


def test_applying_fewer_years_never_downgrades_the_resume():
    after = apply_actions(make_resume(years_of_experience=5), [Action("years", 2)])
    assert after.years_of_experience == 5


def test_applying_years_replaces_the_number():
    after = apply_actions(make_resume(years_of_experience=1), [Action(kind="years", value=4)])
    assert after.years_of_experience == 4


# ---------------------------------------------------------------------------
# Đếm số tin đủ điều kiện
# ---------------------------------------------------------------------------


def test_qualified_count_uses_the_same_rule_as_the_matching_page():
    """Tin đòi N2, CV mới N4 -> chưa đủ; nâng lên N2 -> đủ."""
    jobs = [make_job(required_japanese="business")]
    before = qualified_job_ids(jobs, make_resume(japanese_level="basic"))
    after = qualified_job_ids(jobs, make_resume(japanese_level="business"))

    assert len(before) == 0
    assert len(after) == 1


def test_qualified_count_needs_no_embedder():
    """`is_qualified` thuần luật; mô phỏng không được phụ thuộc service embedder."""
    jobs = [make_job(required_japanese="business", required_skills=["Python"])]
    resume = make_resume(japanese_level="business", skills_normalized=["python"])
    assert len(qualified_job_ids(jobs, resume)) == 1


# ---------------------------------------------------------------------------
# Tính chất trung tâm: lợi ích KHÔNG cộng được
# ---------------------------------------------------------------------------


def test_deltas_do_not_add_up():
    """Học A mở thêm 1 tin, học B mở thêm 1 tin, học cả hai KHÔNG mở thêm 2 tin.

    Tin dưới đây đòi CẢ tiếng Nhật mức nghiệp vụ LẪN kỹ năng Go. Bù một trong
    hai thứ thì vẫn còn điều kiện loại kia chặn, nên lợi ích lẻ của cả hai đều
    bằng 0; bù cả hai mới mở được tin.

    Đây chính là lý do không thể tính sẵn một bảng "học X được lợi bao nhiêu"
    rồi cộng lại: phải chấm lại với đúng tổ hợp mà người dùng chọn.
    """
    jobs = [make_job(required_japanese="business", required_skills=["Go"])]
    resume = make_resume(japanese_level="basic", skills_normalized=["Python"])

    base = len(qualified_job_ids(jobs, resume))
    only_japanese = len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business")])))
    only_skill = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Go")])))
    both = len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business"), Action("skill", "Go")])))

    assert base == 0
    assert only_japanese - base == 0
    assert only_skill - base == 0
    assert both - base == 1
    assert (both - base) != (only_japanese - base) + (only_skill - base)


def test_combining_can_open_MORE_than_the_sum_of_the_parts():
    """Chiều bất ngờ: kết hợp cho nhiều hơn tổng lẻ.

    Đo trên dữ liệu thật: "lên N2" mở thêm 64 tin, "học Sales" mở thêm 42 tin,
    tổng lẻ là 106 — nhưng làm cả hai mở thêm **116** tin. Vì có những tin đòi
    CÙNG LÚC cả hai thứ: bù riêng từng cái thì cái còn lại vẫn chặn, nên chúng
    không được tính vào lợi ích lẻ nào cả.

    Bản thiết kế ban đầu đoán sai chiều (tưởng kết hợp luôn NHỎ hơn tổng lẻ).
    Test này pin lại chiều đúng để câu chữ trên giao diện không nói sai.
    """
    jobs = [
        make_job(required_japanese="business"),  # chỉ cần tiếng Nhật
        make_job(required_skills=["Go"]),  # chỉ cần kỹ năng
        make_job(required_japanese="business", required_skills=["Go"]),  # cần CẢ HAI
    ]
    resume = make_resume(japanese_level="basic", skills_normalized=["Python"])

    base = len(qualified_job_ids(jobs, resume))
    only_jp = len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business")]))) - base
    only_go = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Go")]))) - base
    both = (
        len(qualified_job_ids(jobs, apply_actions(resume, [Action("japanese", "business"), Action("skill", "Go")])))
        - base
    )

    assert (only_jp, only_go) == (1, 1)
    assert both == 3, "tin đòi cả hai điều kiện chỉ mở ra khi bù cả hai"
    assert both > only_jp + only_go


def test_combining_can_open_FEWER_than_the_sum_of_the_parts():
    """Chiều còn lại: hai phương án cùng mở một tin thì không cộng dồn."""
    jobs = [make_job(required_skills=["Go", "Rust"])]
    resume = make_resume(skills_normalized=[])

    base = len(qualified_job_ids(jobs, resume))
    only_go = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Go")]))) - base
    only_rust = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Rust")]))) - base
    both = len(qualified_job_ids(jobs, apply_actions(resume, [Action("skill", "Go"), Action("skill", "Rust")]))) - base

    assert (only_go, only_rust) == (1, 1)
    assert both == 1, "cùng một tin, không được đếm hai lần"
    assert both < only_go + only_rust


# ---------------------------------------------------------------------------
# Sinh phương án
# ---------------------------------------------------------------------------


def test_candidates_never_suggest_a_value_the_api_would_reject():
    """Giao diện không được mời người dùng chọn thứ mà API sẽ trả 400.

    Mốc kinh nghiệm sinh ra bằng "hiện tại + 1/+3", nên CV ghi 49 năm sẽ sinh
    ra mốc 52 — vượt trần MAX_SIMULATED_YEARS mà controller kiểm. Tick vào là
    nhận 400 cho một lựa chọn do chính hệ thống bày ra.
    """
    resume = make_resume(years_of_experience=MAX_SIMULATED_YEARS - 1)
    years = [a.value for a in candidate_actions([make_job()], resume) if a.kind == "years"]

    assert years, "vẫn phải còn ít nhất một mốc dưới trần"
    assert all(y <= MAX_SIMULATED_YEARS for y in years)


def test_candidates_stop_offering_years_at_the_cap():
    resume = make_resume(years_of_experience=MAX_SIMULATED_YEARS)
    assert not [a for a in candidate_actions([make_job()], resume) if a.kind == "years"]


def test_candidates_never_suggest_a_skill_the_resume_already_has():
    jobs = [make_job(required_skills=["Python", "AWS"]) for _ in range(3)]
    resume = make_resume(skills_normalized=["python"])  # khác hoa thường, vẫn phải nhận ra

    skills = [a.value for a in candidate_actions(jobs, resume) if a.kind == "skill"]
    assert "AWS" in skills
    assert not any(s.lower() == "python" for s in skills)


def test_candidates_offer_the_next_japanese_levels_only():
    jobs = [make_job(required_japanese="native")]
    resume = make_resume(japanese_level="conversational")

    levels = [a.value for a in candidate_actions(jobs, resume) if a.kind == "japanese"]
    assert levels == ["business", "fluent"], "chỉ gợi ý hai bậc kế tiếp, không nhảy cóc lên native"


def test_candidates_for_a_resume_without_japanese_skip_the_none_level():
    """`none` là 'không yêu cầu', gợi ý người ta 'học lên mức không yêu cầu' là vô nghĩa."""
    resume = make_resume(japanese_level=None)
    levels = [a.value for a in candidate_actions([make_job()], resume) if a.kind == "japanese"]
    assert "none" not in levels
    assert levels == ["basic", "conversational"]


# ---------------------------------------------------------------------------
# Kết quả mô phỏng
# ---------------------------------------------------------------------------


def test_simulate_reports_salary_of_the_jobs_it_opens():
    """Không bịa số giờ học; chỉ nói hai điều đo được: mở thêm mấy tin, lương bao nhiêu."""
    jobs = [
        make_job(required_skills=["Go"], salary_min=6_000_000),
        make_job(required_skills=["Go"], salary_min=8_000_000),
        make_job(required_skills=["Python"], salary_min=1_000_000),
    ]
    resume = make_resume(skills_normalized=["Python"])

    outcome = simulate(jobs, resume, [Action("skill", "Go")])

    assert outcome["deltaJobs"] == 2
    assert outcome["openedSalaryMedian"] == 8_000_000
    assert outcome["openedSalarySample"] == 2


def test_simulate_with_no_action_is_the_baseline():
    jobs = [make_job(required_skills=["Go"])]
    resume = make_resume(skills_normalized=["Go"])
    outcome = simulate(jobs, resume, [])
    assert outcome["deltaJobs"] == 0
    assert outcome["qualifiedJobs"] == 1


# ---------------------------------------------------------------------------
# Qua API thật
# ---------------------------------------------------------------------------


async def test_whatif_requires_authentication(client):
    assert (await client.get("/api/match/whatif")).status_code == 401


async def test_whatif_requires_a_resume(client, user, has_jobs):
    """Không có CV thì không có gì để mô phỏng — phải nói rõ, không trả rỗng."""
    r = await client.get("/api/match/whatif", headers=user.headers)
    assert r.status_code == 404
    assert r.json()["code"] == "match.noResume"


async def test_whatif_lists_suggestions_sorted_by_benefit(client, user_with_resume, has_jobs):
    r = await client.get("/api/match/whatif", headers=user_with_resume.headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["totalJobs"] > 0
    assert "qualifiedJobs" in body["baseline"]
    deltas = [s["deltaJobs"] for s in body["suggestions"]]
    assert deltas == sorted(deltas, reverse=True), "phải xếp giảm dần theo lợi ích"


async def test_whatif_matches_the_qualified_count_of_the_match_page(client, user_with_resume, has_jobs):
    """Hai màn hình phải nói cùng một con số về cùng một CV.

    Nếu lệch nghĩa là mô phỏng đã dùng một bộ luật khác — đúng loại lỗi không ai
    phát hiện cho tới lúc demo.
    """
    whatif = (await client.get("/api/match/whatif", headers=user_with_resume.headers)).json()
    page = (
        await client.get("/api/match/companies", params={"qualifiedOnly": True}, headers=user_with_resume.headers)
    ).json()
    assert whatif["baseline"]["qualifiedCompanies"] == page["totalCompanies"]


async def test_whatif_combination_is_not_the_sum_of_its_parts(client, user_with_resume, has_jobs):
    """Kiểm trên dữ liệu thật đúng tính chất đã pin ở test logic thuần."""
    body = (await client.get("/api/match/whatif", headers=user_with_resume.headers)).json()
    two = [s for s in body["suggestions"] if s["deltaJobs"] > 0][:2]
    if len(two) < 2:
        pytest.skip("CV mẫu không có đủ 2 phương án sinh lợi để so sánh")

    r = await client.post(
        "/api/match/whatif",
        json={"actions": [{"kind": s["kind"], "value": s["value"]} for s in two]},
        headers=user_with_resume.headers,
    )
    assert r.status_code == 200, r.text
    combined = r.json()
    assert combined["sumOfIndividualDeltas"] == sum(s["deltaJobs"] for s in two)
    # KHÔNG khẳng định lớn hơn hay nhỏ hơn: cả hai chiều đều xảy ra được, xem
    # hai test logic thuần ở trên. Bất biến luôn đúng là kết hợp không bao giờ
    # tệ hơn phương án lẻ tốt nhất — bù thêm một thứ không làm mất cơ hội nào.
    assert combined["combined"]["deltaJobs"] >= max(s["deltaJobs"] for s in two)


@pytest.mark.parametrize(
    "action",
    [
        {"kind": "years", "value": "abc"},  # không ép được sang số -> từng ném 500
        {"kind": "years", "value": None},
        {"kind": "years", "value": -3},  # kinh nghiệm âm là vô nghĩa
        {"kind": "skill", "value": None},  # từng lặng lẽ thêm kỹ năng tên "None"
        {"kind": "skill", "value": ""},
        {"kind": "japanese", "value": "khong_co_bac_nay"},  # từng lặng lẽ bỏ qua
    ],
)
async def test_whatif_rejects_a_malformed_value(client, user_with_resume, has_jobs, action):
    """Giá trị hỏng phải thành 400 có mã, không được thành 500.

    Controller bản đầu chỉ kiểm `kind`, còn `value` đi thẳng vào `int(...)` —
    gửi `{"kind": "years", "value": "abc"}` là ném ValueError giữa luồng xử lý
    và API trả 500.
    """
    r = await client.post(
        "/api/match/whatif",
        json={"actions": [action]},
        headers=user_with_resume.headers,
    )
    assert r.status_code == 400, f"{action} -> {r.status_code}: {r.text[:200]}"
    assert r.json()["code"] == "whatif.invalidValue"


async def test_whatif_rejects_an_unknown_action_kind(client, user_with_resume, has_jobs):
    r = await client.post(
        "/api/match/whatif",
        json={"actions": [{"kind": "salary", "value": 999}]},
        headers=user_with_resume.headers,
    )
    assert r.status_code == 400
    assert r.json()["code"] == "whatif.unknownAction"
