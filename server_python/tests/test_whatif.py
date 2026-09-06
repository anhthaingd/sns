"""Test engine mô phỏng đối chứng — dựng CV và tin bằng tay, không cần DB.

Test quan trọng nhất trong file này là `test_deltas_do_not_add_up`: nó pin lại
đúng cái tính chất khiến chức năng này phải tồn tại dưới dạng một engine chấm
lại, chứ không phải một bảng tra sẵn.
"""

from app.models.job import JobMatchView
from app.models.resume import ResumeMatchView
from app.services.whatif import Action, apply_actions, candidate_actions, qualified_job_ids, simulate
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


# ---------------------------------------------------------------------------
# Sinh phương án
# ---------------------------------------------------------------------------


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
