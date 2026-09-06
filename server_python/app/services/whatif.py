"""Mô phỏng đối chứng: "nếu CV có thêm X thì mở ra bao nhiêu cơ hội?".

Cách làm: nhân bản CV, sửa đúng một trường, rồi chấm lại TOÀN BỘ kho tin bằng
chính `app/services/matching.evaluate` mà trang gợi ý đang dùng. Không có bộ
luật thứ hai — nếu tách đôi, hai màn hình sẽ nói khác nhau về cùng một CV.

**Vì sao phải chấm lại chứ không tra bảng.** Lợi ích của các phương án không
cộng được: một tin đòi cả tiếng Nhật mức nghiệp vụ lẫn Go thì bù riêng từng thứ
đều không mở được tin nào, bù cả hai mới mở được. `tests/test_whatif.py::
test_deltas_do_not_add_up` pin lại tính chất này.

**Không cần embedder.** `MatchResult.is_qualified` chỉ nhìn các `Gap` có
`blocking=True`, không đụng tới vector — nên mọi lời gọi ở đây truyền
`cosine=None`, và con số trả về vẫn đúng nguyên khi service embedder tắt.

**Chi phí.** Đo trên dữ liệu thật: một lượt quét 430 tin mất ~2ms, 15 phương án
là ~22ms. Đủ rẻ để tính ngay trong request, không cần cache.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from app.models.job import LANGUAGE_LEVELS
from app.models.resume import ResumeMatchView
from app.services.matching import evaluate

# Số kỹ năng đưa vào danh sách gợi ý. Nhiều hơn thì màn hình thành một bảng tra
# cứu, mà người dùng chỉ chọn được vài thứ để học.
SKILL_CANDIDATES = 8

# Số bậc ngôn ngữ gợi ý tiếp theo. Gợi ý nhảy thẳng từ N4 lên N1 là không dùng được.
LEVEL_STEPS = 2

# Các mốc kinh nghiệm để mô phỏng.
YEAR_STEPS = (1, 3)


@dataclass
class Action:
    """Một phương án giả định. `value` là dữ liệu thô, giao diện tự dịch."""

    kind: str  # "skill" | "japanese" | "english" | "years"
    value: Any

    def to_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value}


def apply_actions(resume: ResumeMatchView, actions: list[Action]) -> ResumeMatchView:
    """Bản sao của CV đã áp dụng các phương án. KHÔNG sửa bản gốc."""
    draft = resume.model_copy(deep=True)
    for action in actions:
        if action.kind == "skill":
            draft.skills_normalized = [*(draft.skills_normalized or []), str(action.value)]
        elif action.kind == "japanese":
            draft.japanese_level = str(action.value)
        elif action.kind == "english":
            draft.english_level = str(action.value)
        elif action.kind == "years":
            draft.years_of_experience = int(action.value)
    return draft


def qualified_job_ids(jobs: list, resume: ResumeMatchView) -> set:
    """Id của những tin mà CV này qua được vòng lọc điều kiện.

    `cosine=None`: `is_qualified` không dùng tới phần ngữ nghĩa.
    """
    return {job.id for job in jobs if evaluate(job, resume, None).is_qualified}


def _company_key(job) -> str:
    """Gom theo công ty giống hệt `controllers/match.py` để hai màn hình khớp nhau."""
    return str(job.company) if job.company else f"name:{job.company_name or ''}"


def _median(values: list[int]) -> int | None:
    known = sorted(v for v in values if v is not None)
    return known[len(known) // 2] if known else None


def _next_levels(current: str | None, steps: int = LEVEL_STEPS) -> list[str]:
    """Các bậc ngôn ngữ ngay trên mức hiện tại.

    `none` bị loại: nó nghĩa là "tin không yêu cầu", không phải một bậc để học lên.
    """
    index = LANGUAGE_LEVELS.index(current) if current in LANGUAGE_LEVELS else -1
    return [level for level in LANGUAGE_LEVELS[index + 1 :] if level != "none"][:steps]


def candidate_actions(jobs: list, resume: ResumeMatchView) -> list[Action]:
    """Các phương án đáng cân nhắc, chưa xếp hạng.

    Kỹ năng lấy theo NHU CẦU THẬT của kho tin (kỹ năng được nhiều tin đòi nhất
    mà CV chưa có), không lấy theo từ điển — học một thứ không ai tuyển thì mở
    ra 0 cơ hội.
    """
    have = {s.lower() for s in resume.skills_normalized or []}
    demand: Counter = Counter()
    for job in jobs:
        for skill in job.required_skills or []:
            if skill.lower() not in have:
                demand[skill] += 1

    actions = [Action("skill", skill) for skill, _ in demand.most_common(SKILL_CANDIDATES)]
    actions += [Action("japanese", level) for level in _next_levels(resume.japanese_level)]
    actions += [Action("english", level) for level in _next_levels(resume.english_level, steps=1)]

    current_years = resume.years_of_experience or 0
    actions += [Action("years", current_years + step) for step in YEAR_STEPS]
    return actions


def simulate(jobs: list, resume: ResumeMatchView, actions: list[Action]) -> dict:
    """Kết quả khi áp dụng ĐỒNG THỜI các phương án.

    Trả về cả `openedSalaryMedian` — trung vị lương của đúng những tin vừa mở
    ra, tính trên dữ liệu thật. Đây là thứ thay cho "ước lượng số giờ học": số
    giờ thì không có nguồn đáng tin, còn lương của nhóm tin đó thì đo được.
    """
    by_id = {job.id: job for job in jobs}
    before = qualified_job_ids(jobs, resume)
    after = qualified_job_ids(jobs, apply_actions(resume, actions))
    opened = after - before

    opened_salaries = [by_id[jid].salary_min for jid in opened if by_id[jid].salary_min is not None]

    return {
        "actions": [a.to_dict() for a in actions],
        "qualifiedJobs": len(after),
        "qualifiedCompanies": len({_company_key(by_id[jid]) for jid in after}),
        "deltaJobs": len(after) - len(before),
        "openedSalaryMedian": _median(opened_salaries),
        "openedSalarySample": len(opened_salaries),
    }


def suggestions(jobs: list, resume: ResumeMatchView) -> dict:
    """Toàn bộ dữ liệu cho màn hình: hiện trạng + từng phương án đã xếp hạng."""
    before = qualified_job_ids(jobs, resume)
    by_id = {job.id: job for job in jobs}

    rows = []
    for action in candidate_actions(jobs, resume):
        outcome = simulate(jobs, resume, [action])
        outcome.pop("actions")
        rows.append({**action.to_dict(), **outcome})

    rows.sort(key=lambda r: (-r["deltaJobs"], r["kind"]))
    return {
        "totalJobs": len(jobs),
        "baseline": {
            "qualifiedJobs": len(before),
            "qualifiedCompanies": len({_company_key(by_id[jid]) for jid in before}),
        },
        "suggestions": rows,
    }
