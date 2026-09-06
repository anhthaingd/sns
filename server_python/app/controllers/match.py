"""Hai chức năng chính: gợi ý công ty phù hợp, và chỉ ra CV còn thiếu gì.

Cả hai dùng CHUNG một lần chấm điểm (`app/services/matching.evaluate`):
"hợp với công ty nào" là sắp xếp theo điểm, "còn thiếu gì" là mở phần `gaps`
của đúng tin đó ra. Không có hai luồng riêng nên không thể lệch nhau.

Luồng xử lý một request:

    CV -> vector (đã tính sẵn, lưu trong DB)
        -> độ tương đồng với mọi tin (một phép nhân ma trận numpy, <10ms)
        -> chấm điểm từng tin bằng LUẬT + độ tương đồng
        -> gom theo công ty, lấy tin khớp nhất mỗi công ty
"""

import logging
import math

from app.errors import ApiError
from app.models.company import Company
from app.models.job import LANGUAGE_LEVELS, Job, JobMatchView
from app.models.resume import Resume
from app.services.job_index import job_index
from app.services.matching import evaluate
from app.services.whatif import MAX_SIMULATED_YEARS, Action, simulate, suggestions
from app.utils.ids import to_object_id
from app.utils.loaders import load_by_ids
from app.utils.responses import ok

# Nhãn thay cho tên công ty khi tin tuyển dụng ẩn danh nhà tuyển dụng.
UNKNOWN_COMPANY = "Công ty chưa công bố tên"

logger = logging.getLogger("fuurin.match")

PAGE_SIZE = 10


# Chấm nhiều hơn số hiển thị để việc sắp xếp có ý nghĩa, nhưng không chấm vô
# hạn. 420 tin hiện tại nằm gọn trong ngưỡng này.
MAX_JOBS_SCORED = 1000


async def _require_resume(decoded_user: dict) -> Resume:
    resume = await Resume.find_one(Resume.user == to_object_id(decoded_user["_id"], "user_id"))
    if resume is None:
        raise ApiError(404, code="match.noResume")
    return resume


async def _score_all(resume: Resume) -> list[tuple[JobMatchView, object]]:
    """Chấm mọi tin đang hoạt động với CV này, trả về đã sắp xếp giảm dần."""
    similarities = await job_index.similarities(resume.embedding)

    jobs = (
        await Job.find(
            {"is_active": True},
            projection_model=JobMatchView,
        )
        .limit(MAX_JOBS_SCORED)
        .to_list()
    )

    scored = [(job, evaluate(job, resume, similarities.get(job.id))) for job in jobs]
    scored.sort(key=lambda pair: pair[1].score, reverse=True)
    return scored


def _job_summary(job: JobMatchView) -> dict:
    return {
        "_id": str(job.id),
        "title": job.title,
        "url": job.url,
        "source": job.source,
        "company_name": job.company_name,
        "location": job.location,
        "prefecture": job.prefecture,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "employment_type": job.employment_type,
        "remote": job.remote,
        "required_skills": job.required_skills,
        "required_japanese": job.required_japanese,
        "required_english": job.required_english,
        "min_years": job.min_years,
    }


async def match_companies(decoded_user: dict, page: int = 1, qualified_only: bool = False):
    """Chức năng 1 — CV này hợp với công ty nào.

    Gom theo công ty và lấy tin khớp nhất của mỗi công ty: người dùng quan tâm
    "công ty nào hợp với tôi", không phải "20 vị trí của cùng một công ty".
    """
    resume = await _require_resume(decoded_user)
    scored = await _score_all(resume)

    best_per_company: dict[str, tuple[JobMatchView, object]] = {}
    for job, result in scored:
        if qualified_only and not result.is_qualified:
            continue
        # Tin chưa gắn được công ty thì tự đứng riêng theo tên, để không bị gộp
        # nhầm thành một "công ty" khổng lồ không tên.
        key = str(job.company) if job.company else f"name:{job.company_name or UNKNOWN_COMPANY}"
        if key not in best_per_company:
            best_per_company[key] = (job, result)

    ranked = sorted(best_per_company.items(), key=lambda item: item[1][1].score, reverse=True)
    total = len(ranked)
    window = ranked[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    company_map = await load_by_ids(Company, [job.company for _, (job, _) in window if job.company])

    items = []
    for key, (job, result) in window:
        company = company_map.get(key)
        items.append(
            {
                "company": {
                    "_id": str(company.id) if company else None,
                    "name": (company.name if company else job.company_name) or UNKNOWN_COMPANY,
                    "logo_url": company.logo_url if company else None,
                    "website": company.website if company else None,
                    "location": company.location if company else job.location,
                    "description": (company.description[:400] if company and company.description else ""),
                    "tech_stack": company.tech_stack if company else [],
                    "job_count": company.job_count if company else 1,
                },
                "bestJob": _job_summary(job),
                "match": result.to_dict(),
            }
        )

    return ok(
        matches=items,
        totalPage=math.ceil(total / PAGE_SIZE) if total > 0 else 1,
        totalCompanies=total,
        curPage=page,
        # Nói rõ có dùng được phần ngữ nghĩa hay không, để giao diện không tỏ ra
        # thông minh hơn thực tế khi service embedder đang tắt.
        semanticAvailable=bool(resume.embedding) and job_index.size > 0,
    )


async def match_jobs(decoded_user: dict, page: int = 1):
    """Danh sách VIỆC LÀM phù hợp (không gom theo công ty)."""
    resume = await _require_resume(decoded_user)
    scored = await _score_all(resume)

    total = len(scored)
    window = scored[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    return ok(
        matches=[{"job": _job_summary(job), "match": result.to_dict()} for job, result in window],
        totalPage=math.ceil(total / PAGE_SIZE) if total > 0 else 1,
        totalJobs=total,
        curPage=page,
        semanticAvailable=bool(resume.embedding) and job_index.size > 0,
    )


async def job_gap(decoded_user: dict, job_id: str):
    """Chức năng 2 — vào được vị trí này thì CV còn thiếu gì."""
    resume = await _require_resume(decoded_user)
    oid = to_object_id(job_id, "job_id")

    job = await Job.find_one({"_id": oid}, projection_model=JobMatchView)
    if job is None:
        raise ApiError(404, code="job.notFound")

    similarities = await job_index.similarities(resume.embedding)
    result = evaluate(job, resume, similarities.get(oid))

    company = await Company.get(job.company) if job.company else None

    return ok(
        job=_job_summary(job),
        company=(
            {
                "_id": str(company.id),
                "name": company.name,
                "logo_url": company.logo_url,
                "website": company.website,
                "description": company.description[:600] if company.description else "",
                "tech_stack": company.tech_stack,
            }
            if company
            else None
        ),
        match=result.to_dict(),
        qualified=result.is_qualified,
    )


async def company_gap(decoded_user: dict, company_id: str):
    """Chức năng 2 ở mức công ty — tổng hợp thiếu sót trên mọi vị trí đang tuyển."""
    resume = await _require_resume(decoded_user)
    company = await Company.get(to_object_id(company_id, "company_id"))
    if company is None:
        raise ApiError(404, code="company.notFound")

    similarities = await job_index.similarities(resume.embedding)
    jobs = await Job.find(
        {"company": company.id, "is_active": True},
        projection_model=JobMatchView,
    ).to_list()

    if not jobs:
        raise ApiError(404, code="company.noOpenJobs")

    scored = sorted(
        ((job, evaluate(job, resume, similarities.get(job.id))) for job in jobs),
        key=lambda pair: pair[1].score,
        reverse=True,
    )

    # Gộp thiếu sót của mọi vị trí, loại trùng theo nội dung — người dùng cần
    # biết "công ty này nói chung đòi những gì mình chưa có".
    seen: set[str] = set()
    combined = []
    for _, result in scored:
        for gap in result.gaps:
            if gap.message not in seen:
                seen.add(gap.message)
                combined.append(gap.to_dict())

    best_job, best_result = scored[0]
    return ok(
        company={
            "_id": str(company.id),
            "name": company.name,
            "logo_url": company.logo_url,
            "website": company.website,
            "description": company.description[:600] if company.description else "",
            "tech_stack": company.tech_stack,
            "job_count": company.job_count,
        },
        bestJob=_job_summary(best_job),
        bestMatch=best_result.to_dict(),
        positions=[{"job": _job_summary(j), "match": r.to_dict()} for j, r in scored[:10]],
        combinedGaps=combined,
    )


# ---------------------------------------------------------------------------
# Chức năng 3 — bù chỗ nào thì mở ra nhiều cơ hội nhất
# ---------------------------------------------------------------------------

VALID_ACTION_KINDS = {"skill", "japanese", "english", "years"}


def _parse_action(item: dict | None) -> Action:
    """Dựng một `Action` từ dữ liệu client gửi lên, hoặc ném 400.

    Kiểm CẢ `value` chứ không chỉ `kind`: bản đầu để `value` đi thẳng vào
    `int(...)` bên trong engine, nên `{"kind": "years", "value": "abc"}` ném
    ValueError giữa luồng xử lý và API trả 500 thay vì 400.
    """
    item = item or {}
    kind = item.get("kind")
    if kind not in VALID_ACTION_KINDS:
        raise ApiError(400, code="whatif.unknownAction")

    value = item.get("value")
    if kind == "skill":
        if not isinstance(value, str) or not value.strip():
            raise ApiError(400, code="whatif.invalidValue")
        return Action(kind=kind, value=value.strip())

    if kind in ("japanese", "english"):
        if value not in LANGUAGE_LEVELS:
            raise ApiError(400, code="whatif.invalidValue")
        return Action(kind=kind, value=value)

    # years — `bool` là con của `int` trong Python, chặn riêng để `true` không
    # lặng lẽ thành 1 năm kinh nghiệm.
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SIMULATED_YEARS:
        raise ApiError(400, code="whatif.invalidValue")
    return Action(kind=kind, value=value)


async def _active_jobs() -> list[JobMatchView]:
    return await Job.find({"is_active": True}, projection_model=JobMatchView).limit(MAX_JOBS_SCORED).to_list()


async def whatif_suggestions(decoded_user: dict):
    """Xếp các phương án theo số tin mở thêm được.

    Cố ý KHÔNG gọi `job_index.similarities`: số tin đủ điều kiện là thuần luật,
    và việc nó không phụ thuộc embedder là một tính chất cần giữ, không phải
    chuyện tình cờ.
    """
    resume = await _require_resume(decoded_user)
    return ok(**suggestions(await _active_jobs(), resume))


async def whatif_simulate(decoded_user: dict, raw_actions: list[dict] | None):
    """Áp dụng ĐỒNG THỜI một tổ hợp phương án do người dùng chọn."""
    resume = await _require_resume(decoded_user)

    actions = [_parse_action(item) for item in raw_actions or []]

    jobs = await _active_jobs()
    combined = simulate(jobs, resume, actions)

    # Tổng lợi ích lẻ, để giao diện giải thích được vì sao con số kết hợp nhỏ hơn.
    individual = sum(simulate(jobs, resume, [a])["deltaJobs"] for a in actions)

    return ok(
        baseline={"qualifiedJobs": combined["qualifiedJobs"] - combined["deltaJobs"]},
        combined=combined,
        sumOfIndividualDeltas=individual,
    )
