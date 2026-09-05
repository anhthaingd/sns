"""Test lõi chấm điểm — dựng CV và tin bằng tay, không cần DB hay embedder.

Đây là phần quyết định giá trị của cả chức năng, nên phải kiểm được độc lập với
mọi hạ tầng.
"""

import pytest
from app.models.job import JobMatchView
from app.models.resume import ResumeMatchView
from app.services.matching import evaluate, normalize_semantic
from bson import ObjectId

# Dùng lớp view thay vì Document: test lõi chấm điểm không cần Mongo, và cũng
# không nên cần — đây là logic thuần.


def make_job(**kwargs) -> JobMatchView:
    defaults = {"_id": ObjectId(), "url": "https://example.com/1", "title": "Backend Engineer"}
    return JobMatchView(**{**defaults, **kwargs})


def make_resume(**kwargs) -> ResumeMatchView:
    return ResumeMatchView(**kwargs)


# ---------------------------------------------------------------------------
# Điều kiện cứng — chỗ mà embedding KHÔNG làm được
# ---------------------------------------------------------------------------


def test_japanese_requirement_blocks_when_resume_is_lower():
    job = make_job(required_japanese="business")
    result = evaluate(job, make_resume(japanese_level="basic"), cosine=0.5)

    gap = next(g for g in result.gaps if g.kind == "japanese_level")
    assert gap.blocking is True
    assert "Nghiệp vụ" in gap.required
    assert not result.is_qualified


def test_japanese_requirement_is_met_when_resume_is_higher():
    job = make_job(required_japanese="conversational")
    result = evaluate(job, make_resume(japanese_level="fluent"), cosine=0.5)

    assert not [g for g in result.gaps if g.kind == "japanese_level"]
    assert result.is_qualified


def test_two_identical_resumes_differing_only_in_japanese_get_different_scores():
    """Đây chính là thứ embedding thuần không phân biệt được.

    Đo được trên dữ liệu thật: hai CV chỉ khác dòng "Japanese: none" / "N1" có
    độ tương đồng vector 0.9871, tức là embedding coi hai người gần như một.
    Tầng luật phải tách được hai người đó ra.
    """
    job = make_job(required_japanese="business")
    same_cosine = 0.55

    with_japanese = evaluate(job, make_resume(japanese_level="fluent"), same_cosine)
    without_japanese = evaluate(job, make_resume(japanese_level=None), same_cosine)

    assert with_japanese.score > without_japanese.score
    assert with_japanese.is_qualified and not without_japanese.is_qualified


def test_unknown_requirement_is_not_counted_against_the_candidate():
    """Tin không ghi yêu cầu tiếng Nhật (79% tin lúc chưa làm giàu dữ liệu).

    Chấm người ta "chưa đạt" vì TIN thiếu thông tin là sai.
    """
    job = make_job(required_japanese=None, required_skills=["Python"])
    result = evaluate(job, make_resume(skills_normalized=["Python"]), cosine=0.5)

    assert not [g for g in result.gaps if g.kind == "japanese_level"]
    assert result.requirement_ratio == 1.0


def test_job_requiring_no_japanese_is_always_satisfied():
    job = make_job(required_japanese="none")
    result = evaluate(job, make_resume(japanese_level=None), cosine=0.4)
    assert result.is_qualified


# ---------------------------------------------------------------------------
# Kỹ năng và kinh nghiệm
# ---------------------------------------------------------------------------


def test_missing_skills_are_listed_by_name():
    job = make_job(required_skills=["Python", "Kubernetes", "Terraform"])
    result = evaluate(job, make_resume(skills_normalized=["Python"]), cosine=0.5)

    gap = next(g for g in result.gaps if g.kind == "missing_skill")
    assert "Kubernetes" in gap.message and "Terraform" in gap.message
    assert "Python" not in gap.message.split(":")[1]
    # Thiếu một phần thì học được, không phải điều kiện loại.
    assert gap.blocking is False


def test_zero_skill_overlap_is_blocking():
    job = make_job(required_skills=["Kubernetes", "Terraform"])
    result = evaluate(job, make_resume(skills_normalized=["Teaching"]), cosine=0.2)
    assert next(g for g in result.gaps if g.kind == "missing_skill").blocking is True


def test_experience_gap_says_how_many_years_are_missing():
    job = make_job(min_years=5)
    result = evaluate(job, make_resume(years_of_experience=2), cosine=0.5)

    gap = next(g for g in result.gaps if g.kind == "experience_years")
    assert "thiếu 3 năm" in gap.message.lower()


def test_no_experience_required_is_satisfied_by_fresher():
    job = make_job(min_years=0)
    result = evaluate(job, make_resume(years_of_experience=None), cosine=0.5)
    assert not [g for g in result.gaps if g.kind == "experience_years"]


# ---------------------------------------------------------------------------
# Điểm mềm — nói cho biết chứ không loại
# ---------------------------------------------------------------------------


def test_salary_and_location_are_reported_but_never_blocking():
    job = make_job(salary_max=3_000_000, prefecture="Osaka")
    resume = make_resume(desired_salary_min=6_000_000, desired_locations=["Tokyo"])
    result = evaluate(job, resume, cosine=0.5)

    kinds = {g.kind for g in result.gaps}
    assert {"salary", "location"} <= kinds
    assert all(not g.blocking for g in result.gaps if g.kind in {"salary", "location"})
    assert result.is_qualified


# ---------------------------------------------------------------------------
# Cách tính điểm
# ---------------------------------------------------------------------------


def test_score_falls_back_to_rules_when_embedder_is_unavailable():
    """Embedder chết thì vẫn phải chấm được — chỉ là kém tinh tế hơn."""
    job = make_job(required_japanese="business", required_skills=["Python"])
    resume = make_resume(japanese_level="fluent", skills_normalized=["Python"])

    result = evaluate(job, resume, cosine=None)

    assert result.semantic_available is False
    assert result.score == pytest.approx(100.0)
    assert result.is_qualified


def test_score_uses_only_semantics_when_job_states_no_requirement():
    job = make_job()
    result = evaluate(job, make_resume(), cosine=0.60)
    assert result.requirement_ratio is None
    assert result.score == pytest.approx(100.0)


@pytest.mark.parametrize(
    ("cosine", "expected"),
    [(None, 0.0), (0.0, 0.0), (0.10, 0.0), (0.35, 0.5), (0.60, 1.0), (0.95, 1.0)],
)
def test_normalize_semantic_calibration(cosine, expected):
    """Hiệu chuẩn theo số đo thật: tin cùng ngành ~0.35-0.65, khác ngành ~0.05-0.15."""
    assert normalize_semantic(cosine) == pytest.approx(expected, abs=0.01)


def test_better_candidate_scores_higher_on_the_same_job():
    job = make_job(required_japanese="business", required_skills=["Python", "AWS"], min_years=3)
    strong = make_resume(japanese_level="native", skills_normalized=["Python", "AWS"], years_of_experience=6)
    weak = make_resume(japanese_level="basic", skills_normalized=["Teaching"], years_of_experience=0)

    assert evaluate(job, strong, 0.5).score > evaluate(job, weak, 0.5).score
