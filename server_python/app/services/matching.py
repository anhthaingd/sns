"""Chấm độ phù hợp giữa CV và tin tuyển dụng, và chỉ ra chỗ còn thiếu.

Điểm gồm hai phần, cố ý tách bạch để giải thích được:

    điểm = 0.55 × (mức liên quan ngữ nghĩa) + 0.45 × (tỷ lệ đáp ứng yêu cầu)

**Vì sao phải có phần thứ hai.** Đo trên chính dữ liệu này: hai CV giống hệt
nhau, chỉ khác một dòng "Japanese: none" và "Japanese: N1", có độ tương đồng
vector là **0.9871** — embedding coi hai người đó gần như một. Danh sách gợi ý
cho họ trùng nhau 4/5. Embedding đo *độ liên quan về chủ đề*, không đo *độ đáp
ứng yêu cầu*. Nên JLPT, số năm kinh nghiệm, lương, địa điểm phải kiểm bằng luật.

**Không lọc bỏ tin chưa đủ điều kiện.** Chức năng "tôi còn thiếu gì để vào công
ty A" chỉ có nghĩa khi người dùng nhìn thấy cả những chỗ mình chưa với tới.
Tin không đạt bị xếp hạng thấp và gắn nhãn, chứ không biến mất.
"""

from dataclasses import asdict, dataclass, field

from app.models.job import LANGUAGE_LEVELS
from app.models.resume import ResumeMatchView

# --- nhãn hiển thị ----------------------------------------------------------

LEVEL_LABELS = {
    "none": "Không yêu cầu",
    "basic": "Cơ bản (N4-N5)",
    "conversational": "Giao tiếp (N3)",
    "business": "Nghiệp vụ (N2)",
    "fluent": "Thành thạo (N1)",
    "native": "Bản ngữ",
}
ENGLISH_LABELS = {
    "none": "Không yêu cầu",
    "basic": "Cơ bản",
    "conversational": "Giao tiếp",
    "business": "Nghiệp vụ",
    "fluent": "Thành thạo",
    "native": "Bản ngữ",
}

# Trọng số giữa các nhóm yêu cầu. Ngôn ngữ nặng nhất vì ở thị trường Nhật đó là
# điều kiện loại trực tiếp, không phải điểm cộng.
WEIGHT_JAPANESE = 3.0
WEIGHT_ENGLISH = 1.5
WEIGHT_SKILLS = 2.5
WEIGHT_YEARS = 1.5

SEMANTIC_WEIGHT = 0.55
REQUIREMENT_WEIGHT = 0.45

# Hiệu chuẩn từ số đo thật trên tập dữ liệu này: cosine của tin cùng ngành nằm
# quanh 0.35-0.65, tin khác hẳn ngành quanh 0.05-0.15. Trải khoảng đó ra 0-1 để
# điểm hiển thị có ý nghĩa với người đọc, thay vì lúc nào cũng quanh quẩn 40%.
SEMANTIC_FLOOR = 0.10
SEMANTIC_CEILING = 0.60


def _level_rank(level: str | None) -> int | None:
    if level is None:
        return None
    try:
        return LANGUAGE_LEVELS.index(level)
    except ValueError:
        return None


@dataclass
class Gap:
    """Một chỗ CV chưa đáp ứng được."""

    kind: str
    message: str
    required: str = ""
    current: str = ""
    # `blocking=True`: hồ sơ gần như chắc chắn bị loại nếu không bù được.
    blocking: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MatchResult:
    score: float
    semantic: float
    requirement_ratio: float | None
    met: list[str] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
    # Không có vector (embedder tắt) thì điểm chỉ dựa vào luật — nói rõ ra để
    # không ai hiểu nhầm là hệ thống đã "hiểu" nội dung CV.
    semantic_available: bool = True

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "semantic": round(self.semantic, 3),
            "requirementRatio": round(self.requirement_ratio, 3) if self.requirement_ratio is not None else None,
            "semanticAvailable": self.semantic_available,
            "met": self.met,
            "gaps": [g.to_dict() for g in self.gaps],
        }

    @property
    def is_qualified(self) -> bool:
        return not any(g.blocking for g in self.gaps)


def _check_language(
    required: str | None,
    current: str | None,
    labels: dict[str, str],
    name: str,
    kind: str,
) -> tuple[float, str | None, Gap | None]:
    """Trả về (điểm 0-1, mô tả nếu đạt, gap nếu chưa đạt).

    Yêu cầu không rõ (`required is None`) thì KHÔNG tính vào điểm — chấm một
    người là "chưa đạt" vì tin không ghi rõ là sai.
    """
    required_rank = _level_rank(required)
    if required_rank is None:
        return 0.0, None, None
    if required == "none":
        return 1.0, f"{name}: không yêu cầu", None

    current_rank = _level_rank(current)
    if current_rank is None:
        return (
            0.0,
            None,
            Gap(
                kind=kind,
                message=f"Tin yêu cầu {name} mức {labels.get(required, required)}, CV chưa ghi trình độ",
                required=labels.get(required, required),
                current="chưa ghi",
                blocking=True,
            ),
        )
    if current_rank >= required_rank:
        return 1.0, f"{name} {labels.get(current, current)} — đạt yêu cầu", None

    return (
        0.0,
        None,
        Gap(
            kind=kind,
            message=(f"Cần {name} mức {labels.get(required, required)}, CV đang ở mức {labels.get(current, current)}"),
            required=labels.get(required, required),
            current=labels.get(current, current),
            blocking=True,
        ),
    )


def _check_skills(required: list[str], current: list[str]) -> tuple[float, str | None, Gap | None]:
    if not required:
        return 0.0, None, None

    have = {s.lower() for s in current or []}
    missing = [s for s in required if s.lower() not in have]
    matched = [s for s in required if s.lower() in have]
    ratio = len(matched) / len(required)

    met = f"Khớp {len(matched)}/{len(required)} kỹ năng: {', '.join(matched)}" if matched else None
    if not missing:
        return 1.0, met, None

    return (
        ratio,
        met,
        Gap(
            kind="missing_skill",
            message="Thiếu kỹ năng: " + ", ".join(missing),
            required=", ".join(required),
            current=", ".join(matched) or "chưa có kỹ năng nào trong danh sách",
            # Thiếu kỹ năng hiếm khi loại thẳng — học được, và tin thường liệt kê cả
            # "nice to have". Nhưng không khớp gì cả thì gần như chắc trượt.
            blocking=ratio == 0,
        ),
    )


def _check_years(required: int | None, current: int | None) -> tuple[float, str | None, Gap | None]:
    if required is None:
        return 0.0, None, None
    if required == 0:
        return 1.0, "Không yêu cầu kinh nghiệm", None
    if current is None:
        return (
            0.0,
            None,
            Gap(
                kind="experience_years",
                message=f"Tin yêu cầu {required} năm kinh nghiệm, CV chưa ghi số năm",
                required=f"{required} năm",
                current="chưa ghi",
            ),
        )
    if current >= required:
        return 1.0, f"{current} năm kinh nghiệm — đạt yêu cầu {required} năm", None

    return (
        current / required,
        None,
        Gap(
            kind="experience_years",
            message=f"Cần {required} năm kinh nghiệm, CV có {current} năm (còn thiếu {required - current} năm)",
            required=f"{required} năm",
            current=f"{current} năm",
            blocking=current == 0,
        ),
    )


def _soft_checks(job, resume: ResumeMatchView) -> list[Gap]:
    """Những điểm lệch đáng nói nhưng không phải điều kiện loại."""
    gaps: list[Gap] = []

    if resume.desired_salary_min and job.salary_max and job.salary_max < resume.desired_salary_min:
        gaps.append(
            Gap(
                kind="salary",
                message=(
                    f"Mức lương tối đa {job.salary_max // 10_000} man/năm thấp hơn mong muốn "
                    f"{resume.desired_salary_min // 10_000} man/năm"
                ),
                required=str(job.salary_max),
                current=str(resume.desired_salary_min),
            )
        )

    if resume.desired_locations and job.prefecture and job.prefecture not in resume.desired_locations:
        gaps.append(
            Gap(
                kind="location",
                message=f"Nơi làm việc {job.prefecture} không nằm trong khu vực mong muốn",
                required=job.prefecture,
                current=", ".join(resume.desired_locations),
            )
        )

    return gaps


def normalize_semantic(cosine: float | None) -> float:
    if cosine is None:
        return 0.0
    scaled = (cosine - SEMANTIC_FLOOR) / (SEMANTIC_CEILING - SEMANTIC_FLOOR)
    return max(0.0, min(1.0, scaled))


def evaluate(job, resume: ResumeMatchView, cosine: float | None = None) -> MatchResult:
    """Chấm một tin tuyển dụng với một CV.

    `job` là `Job` hoặc `JobMatchView`, `resume` là `Resume` hoặc
    `ResumeMatchView` — chỉ cần có đủ các trường được khai báo ở hai lớp view.
    """
    weighted: list[tuple[float, float]] = []
    met: list[str] = []
    gaps: list[Gap] = []

    for weight, (value, ok_text, gap) in [
        (
            WEIGHT_JAPANESE,
            _check_language(job.required_japanese, resume.japanese_level, LEVEL_LABELS, "Tiếng Nhật", "japanese_level"),
        ),
        (
            WEIGHT_ENGLISH,
            _check_language(job.required_english, resume.english_level, ENGLISH_LABELS, "Tiếng Anh", "english_level"),
        ),
        (WEIGHT_SKILLS, _check_skills(job.required_skills or [], resume.skills_normalized or [])),
        (WEIGHT_YEARS, _check_years(job.min_years, resume.years_of_experience)),
    ]:
        if ok_text is None and gap is None and value == 0.0:
            # Tin không nói gì về tiêu chí này -> bỏ qua, không tính vào mẫu số.
            continue
        weighted.append((weight, value))
        if ok_text:
            met.append(ok_text)
        if gap:
            gaps.append(gap)

    gaps.extend(_soft_checks(job, resume))

    total_weight = sum(w for w, _ in weighted)
    requirement_ratio = (sum(w * v for w, v in weighted) / total_weight) if total_weight else None

    semantic = normalize_semantic(cosine)
    if requirement_ratio is None:
        # Tin không nêu yêu cầu nào đo được -> chỉ còn phần ngữ nghĩa.
        score = semantic * 100
    elif cosine is None:
        score = requirement_ratio * 100
    else:
        score = (SEMANTIC_WEIGHT * semantic + REQUIREMENT_WEIGHT * requirement_ratio) * 100

    return MatchResult(
        score=score,
        semantic=semantic,
        requirement_ratio=requirement_ratio,
        met=met,
        gaps=gaps,
        semantic_available=cosine is not None,
    )
