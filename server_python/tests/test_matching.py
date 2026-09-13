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


# ---------------------------------------------------------------------------
# Gộp thiếu sót ở mức CÔNG TY
# ---------------------------------------------------------------------------


def _company_scored(jobs_and_resumes):
    """Dựng danh sách `(job, MatchResult)` đúng hình dạng mà controller truyền vào."""
    return [(job, evaluate(job, resume, cosine=0.5)) for job, resume in jobs_and_resumes]


def test_company_gaps_count_positions_per_missing_skill():
    """Mỗi kỹ năng thiếu là MỘT dòng, kèm số vị trí đang đòi nó.

    Bản cũ gộp bằng cách loại trùng theo nguyên câu `"Thiếu kỹ năng: A, B, C"`.
    Hai tin cùng thiếu Java mà khác nhau đúng một kỹ năng thứ hai cho hai câu
    khác nhau nên cả hai cùng lọt: đo trên dữ liệu thật, một công ty 10 vị trí
    đẻ ra 76 dòng và người đọc không rút ra được mình cần học gì.
    """
    from app.controllers.match import _combine_gaps

    resume = make_resume(skills_normalized=["python"], japanese_level="fluent", years_of_experience=9)
    scored = _company_scored(
        [
            (make_job(required_skills=["Java", "Kotlin"]), resume),
            (make_job(required_skills=["Java", "Spring"]), resume),
            (make_job(required_skills=["Java"]), resume),
        ]
    )

    combined = _combine_gaps(scored)
    skills = [g for g in combined if g["kind"] == "missing_skill"]

    by_skill = {g["params"]["skill"]: g["params"] for g in skills}
    assert set(by_skill) == {"Java", "Kotlin", "Spring"}, by_skill
    assert by_skill["Java"]["count"] == 3, "Java bị ba vị trí đòi nhưng không đếm đủ"
    assert by_skill["Kotlin"]["count"] == 1
    assert by_skill["Java"]["total"] == 3

    # Kỹ năng nhiều vị trí đòi nhất phải đứng đầu: đó là câu trả lời cho
    # "học cái nào thì mở ra nhiều cửa nhất".
    assert skills[0]["params"]["skill"] == "Java"


def test_company_gaps_do_not_repeat_the_same_language_requirement():
    """Mười tin cùng đòi tiếng Nhật N2 là MỘT dòng, không phải mười."""
    from app.controllers.match import _combine_gaps

    resume = make_resume(japanese_level="basic", skills_normalized=["python"])
    scored = _company_scored(
        [(make_job(required_japanese="business", required_skills=["Python"]), resume) for _ in range(10)]
    )

    combined = _combine_gaps(scored)
    language = [g for g in combined if g["kind"] == "japanese_level"]
    assert len(language) == 1, f"yêu cầu tiếng Nhật bị lặp {len(language)} lần"
    assert language[0]["blocking"] is True


def test_company_skill_gaps_are_never_blocking():
    """Ở mức công ty, kỹ năng là "nên học", không phải điều kiện loại.

    Nhãn `blocking` sinh ra ở mức TỪNG TIN: "CV khớp 0 kỹ năng của tin này".
    Đưa nguyên lên mức công ty thì mất nghĩa — chỗ nào có cả trăm vị trí khác
    nhau, gần như kỹ năng nào cũng thuộc về một tin mà CV khớp 0. Đo trên dữ
    liệu thật: 75 trong 91 dòng bị gắn "bắt buộc phải bù", tức nhãn đó không
    còn phân loại được gì nữa.
    """
    from app.controllers.match import _combine_gaps

    resume = make_resume(skills_normalized=["python"], japanese_level="fluent", years_of_experience=9)
    scored = _company_scored(
        [
            (make_job(required_skills=["Python", "Java"]), resume),
            (make_job(required_skills=["Rust"]), resume),  # khớp 0 kỹ năng
        ]
    )

    skills = [g for g in _combine_gaps(scored) if g["kind"] == "missing_skill"]
    assert skills, "không còn dòng kỹ năng nào"
    assert all(g["blocking"] is False for g in skills), "kỹ năng không được là điều kiện loại ở mức công ty"


def test_company_keeps_only_the_easiest_bar_for_a_scaled_requirement():
    """Nhiều vị trí đòi số năm khác nhau -> MỘT dòng, lấy mốc thấp nhất.

    Người dùng cần biết "cửa thấp nhất vẫn cao hơn mình bao nhiêu". Liệt kê đủ
    mọi mốc chỉ ra một chồng dòng "cần 4 / 5 / 8 / 30 năm" chồng lên nhau.
    """
    from app.controllers.match import _combine_gaps

    resume = make_resume(years_of_experience=3, japanese_level="fluent", skills_normalized=["python"])
    scored = _company_scored([(make_job(min_years=y, required_skills=["Python"]), resume) for y in (30, 8, 5, 4)])

    years = [g for g in _combine_gaps(scored) if g["kind"] == "experience_years"]
    assert len(years) == 1, f"số năm kinh nghiệm bị lặp {len(years)} lần"
    assert years[0]["params"]["required"] == 4, "phải giữ mốc dễ nhất, không phải mốc đầu tiên gặp"


def test_company_keeps_only_the_lowest_language_bar():
    """Công ty có vị trí đòi N1, vị trí đòi N2 -> chỉ hiện mốc N2."""
    from app.controllers.match import _combine_gaps

    resume = make_resume(japanese_level="basic", skills_normalized=["python"])
    scored = _company_scored(
        [
            (make_job(required_japanese="fluent", required_skills=["Python"]), resume),
            (make_job(required_japanese="business", required_skills=["Python"]), resume),
        ]
    )

    japanese = [g for g in _combine_gaps(scored) if g["kind"] == "japanese_level"]
    assert len(japanese) == 1
    assert japanese[0]["params"]["requiredLevel"] == "business"


def test_company_keeps_only_the_best_paying_position():
    """Nhiều vị trí trả thấp hơn mong muốn -> MỘT dòng, lấy vị trí trả cao nhất.

    Bốn dòng "lương tối đa 380 / 400 / 450 / 500 man thấp hơn mong muốn 550"
    chồng lên nhau không nói thêm được gì so với một dòng "cao nhất là 500".
    """
    from app.controllers.match import _combine_gaps

    resume = make_resume(desired_salary_min=5_500_000, japanese_level="fluent", skills_normalized=["python"])
    scored = _company_scored(
        [
            (make_job(salary_max=s, required_skills=["Python"]), resume)
            for s in (3_800_000, 4_000_000, 4_500_000, 5_000_000)
        ]
    )

    salary = [g for g in _combine_gaps(scored) if g["kind"] == "salary"]
    assert len(salary) == 1, f"mức lương bị lặp {len(salary)} lần"
    assert salary[0]["params"]["jobMax"] == 500, "phải giữ vị trí trả cao nhất"
