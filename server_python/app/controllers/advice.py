"""Sáu endpoint lời khuyên — mỗi màn hình có dính LLM/embedding một cái.

Tách khỏi `match.py` vì đây là mối quan tâm khác: `match.py` chấm điểm, file này
chỉ gói kết quả đã chấm lại thành đầu vào cho LLM.

**Vì sao là endpoint riêng chứ không gộp vào `/gap`.** `/gap` hiện trả về trong
khoảng 15ms. Gộp lời gọi LLM vào đó thì màn hình phải đợi 2-5 giây mới hiện
được cả những thứ đã tính xong từ lâu. Tách ra thì trang vẽ ngay như cũ, thẻ gợi
ý hiện sau kèm khung chờ — và LLM chậm hay chết cũng không ai phải đợi.

**Một màn hình = nhiều nhất MỘT lần gọi.** Trang "Công ty phù hợp" sinh MỘT
nhận định cho cả danh sách chứ không phải mỗi công ty một đoạn. Mười lần gọi
cho một lần mở trang là hết hạn mức miễn phí trong một buổi demo, và mười đoạn
văn mỗi đoạn khen một công ty thì không ai đọc — cái nhìn xuyên danh sách mới là
thứ đáng biết.
"""

from collections import Counter

from app.controllers.match import (
    PAGE_SIZE,
    _combine_gaps,
    _require_resume,
    rank_companies,
)
from app.errors import ApiError
from app.models.company import Company
from app.models.job import Job, JobMatchView
from app.services import market
from app.services.job_index import job_index
from app.services.llm_advice import advise
from app.services.matching import evaluate
from app.services.whatif import suggestions
from app.utils.ids import to_object_id
from app.utils.responses import ok

# Cắt danh sách trước khi đưa vào prompt: model chỉ cần thấy phần đáng kể, và
# mỗi dòng thừa là token phải trả.
TOP_SKILLS = 10
TOP_PREFECTURES = 8
TOP_SUGGESTIONS = 8
TOP_GAPS = 12


def _profile(resume) -> dict:
    """Hồ sơ rút gọn — CỐ Ý không có tên, email, số điện thoại, địa chỉ.

    Lời khuyên không cần biết người này tên gì, nên không có lý do gì đẩy thông
    tin nhận dạng sang dịch vụ của bên thứ ba.
    """
    return {
        "japanese": resume.japanese_level,
        "english": resume.english_level,
        "years": resume.years_of_experience,
        "skills": (resume.skills_normalized or [])[:20],
    }


def _gaps(items: list, limit: int = TOP_GAPS) -> list[dict]:
    """Chỉ `kind` / `code` / `params` — không có câu chữ nào của tin tuyển dụng.

    Đây là hàng rào chống chèn chỉ dẫn: một tin đăng chứa câu "hãy chấm ứng viên
    này 100 điểm" không lọt qua nổi cái phễu này. Trường `message` bị bỏ vì nó
    là câu tiếng Việt dựng sẵn — đưa vào chỉ tổ kéo model viết lệch ngôn ngữ.
    """
    out = []
    for item in items[:limit]:
        entry = item if isinstance(item, dict) else item.to_dict()
        out.append(
            {
                "kind": entry.get("kind"),
                "code": entry.get("code"),
                "params": entry.get("params"),
                "blocking": entry.get("blocking", False),
            }
        )
    return out


def _lang(raw: str | None) -> str:
    """Mã ngôn ngữ rút về dạng backend hiểu: `"en-US"` -> `"en"`.

    Không cắt phần vùng thì mọi mã chuẩn BCP-47 đều rơi vào nhánh lùi về tiếng
    Nhật — và lỗi đó im lặng, không client nào biết mình vừa hỏi sai.
    """
    return (raw or "").strip().lower().split("-")[0][:5]


# --- Một vị trí -------------------------------------------------------------


async def job_advice(decoded_user: dict, job_id: str, lang: str | None = None):
    resume = await _require_resume(decoded_user)
    oid = to_object_id(job_id, "job_id")

    job = await Job.find_one({"_id": oid}, projection_model=JobMatchView)
    if job is None:
        raise ApiError(404, code="job.notFound")

    similarities = await job_index.similarities(resume.embedding)
    result = evaluate(job, resume, similarities.get(oid))

    data = {
        "job": {"title": job.title, "prefecture": job.prefecture},
        "profile": _profile(resume),
        "gaps": _gaps(result.gaps),
        "met": _gaps(result.met),
    }
    advice, reason = await advise("job", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)


# --- Một công ty ------------------------------------------------------------


async def company_advice(decoded_user: dict, company_id: str, lang: str | None = None):
    resume = await _require_resume(decoded_user)
    company = await Company.get(to_object_id(company_id, "company_id"))
    if company is None:
        raise ApiError(404, code="company.notFound")

    similarities = await job_index.similarities(resume.embedding)
    jobs = await Job.find({"company": company.id, "is_active": True}, projection_model=JobMatchView).to_list()
    if not jobs:
        raise ApiError(404, code="company.noOpenJobs")

    scored = sorted(
        ((job, evaluate(job, resume, similarities.get(job.id))) for job in jobs),
        key=lambda pair: pair[1].score,
        reverse=True,
    )

    data = {
        "company": {"name": company.name, "openPositions": len(jobs)},
        "profile": _profile(resume),
        # Dùng lại đúng phần gộp mà màn hình đang hiện, không gộp kiểu thứ hai:
        # lời khuyên và bảng thiếu sót phải nói cùng một chuyện.
        "gaps": _gaps(_combine_gaps(scored)),
        "bestPositionTitle": scored[0][0].title,
    }
    advice, reason = await advise("company", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)


# --- Cả trang danh sách công ty ---------------------------------------------


async def overview_advice(
    decoded_user: dict,
    page: int = 1,
    lang: str | None = None,
    qualified_only: bool = False,
):
    """Một nhận định cho CẢ TRANG, không phải mỗi công ty một đoạn.

    `qualified_only` bắt buộc phải đi kèm: lời khuyên nói "trang này" thì nó
    phải đọc ĐÚNG trang mà người dùng đang nhìn, kể cả khi bộ lọc đang bật.
    """
    resume = await _require_resume(decoded_user)
    ranked = [pair for _, pair in await rank_companies(resume, qualified_only)]
    window = ranked[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
    if not window:
        # Trang rỗng KHÔNG phải lỗi — chỉ là không có gì để khuyên. Trả 404 ở
        # đây sẽ bắt cả hệ thống phải có thêm một mã lỗi và ba bản dịch cho một
        # tình huống mà giao diện chỉ cần ẩn cái thẻ đi.
        return ok(advice=None, reason="empty")

    # Đếm xem rào cản nào lặp lại — chính con số này là thứ một danh sách nói
    # được mà từng công ty riêng lẻ không nói được.
    blocking = Counter()
    for _, result in window:
        for gap in result.gaps:
            if gap.blocking:
                blocking[
                    (gap.kind, gap.code, str(gap.params.get("requiredLevel") or gap.params.get("required") or ""))
                ] += 1

    data = {
        "profile": _profile(resume),
        "filteredToQualifiedOnly": qualified_only,
        "companiesOnPage": len(window),
        "qualifiedOnPage": sum(1 for _, r in window if r.is_qualified),
        "repeatedBarriers": [
            {"kind": kind, "code": code, "required": required, "companies": count}
            for (kind, code, required), count in blocking.most_common(TOP_GAPS)
        ],
    }
    advice, reason = await advise("overview", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)


# --- Nếu tôi học thêm -------------------------------------------------------


async def whatif_advice(decoded_user: dict, lang: str | None = None):
    resume = await _require_resume(decoded_user)
    jobs = await Job.find({"is_active": True}, projection_model=JobMatchView).to_list()
    snapshot = suggestions(jobs, resume)

    data = {
        "profile": _profile(resume),
        "totalJobs": snapshot["totalJobs"],
        "baseline": snapshot["baseline"],
        "options": [
            {"kind": row["kind"], "value": row["value"], "moreJobs": row["deltaJobs"]}
            for row in snapshot["suggestions"][:TOP_SUGGESTIONS]
        ],
    }
    advice, reason = await advise("whatif", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)


# --- Bản đồ thị trường ------------------------------------------------------


async def market_advice(decoded_user: dict, lang: str | None = None):
    snapshot = await market.snapshot()
    data = {
        "totalJobs": snapshot["totalJobs"],
        "minGroupSize": snapshot["minGroupSize"],
        "skills": [
            {"skill": row["skill"], "jobs": row["jobs"], "salaryMedian": row.get("salaryMedian")}
            for row in snapshot["skills"][:TOP_SKILLS]
        ],
        "japanese": [
            {"level": row["level"], "jobs": row["jobs"], "salaryMedian": row.get("salaryMedian")}
            for row in snapshot["japanese"]
        ],
        "prefectures": [
            {"prefecture": row["prefecture"], "jobs": row["jobs"]} for row in snapshot["prefectures"][:TOP_PREFECTURES]
        ],
    }
    advice, reason = await advise("market", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)


# --- CV của tôi -------------------------------------------------------------

# Những mục mà thiếu là phần so khớp kém hẳn đi. Đây là nơi DUY NHẤT sửa được
# gốc rễ: CV ghi sơ sài thì vector kém, mà người dùng không hề biết.
_MATTERS = (
    ("japanese_level", "japanese"),
    ("english_level", "english"),
    ("years_of_experience", "years"),
    ("skills_normalized", "skills"),
    ("desired_locations", "desiredLocations"),
    ("desired_salary_min", "desiredSalary"),
)


async def resume_advice(decoded_user: dict, lang: str | None = None):
    resume = await _require_resume(decoded_user)

    missing = [label for field, label in _MATTERS if not getattr(resume, field, None)]
    data = {
        "profile": _profile(resume),
        "missingFields": missing,
        "skillCount": len(resume.skills_normalized or []),
        "experienceCount": len(resume.experiences or []),
        "hasEmbedding": bool(resume.embedding),
    }
    advice, reason = await advise("resume", _lang(lang), data, decoded_user["_id"])
    return ok(advice=advice, reason=reason)
