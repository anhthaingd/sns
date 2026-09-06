"""Tra cứu tin tuyển dụng và doanh nghiệp đã được ETL chuẩn hoá.

Thay cho chức năng crawl trực tiếp trước đây: nhanh hơn (đọc DB thay vì mở
trình duyệt), tìm kiếm và lọc được, và không chết theo trang nguồn.
"""

import math

from app.errors import ApiError
from app.models.company import Company
from app.models.job import Job
from app.utils.ids import to_object_id
from app.utils.loaders import load_by_ids
from app.utils.responses import ok
from app.utils.search import contains, normalize_search
from app.utils.serialization import serialize_doc

# 12 thay vì 10 như các controller khác: danh sách việc làm hiển thị dạng
# lưới 2 cột nên số chẵn chia hết cho 2 mới lấp đầy hàng cuối.
PAGE_SIZE = 12

# Không bao giờ trả vector ra API: 384 số thực mỗi bản ghi, người dùng không
# dùng tới, mà payload thì phình lên vài MB.
HIDDEN_FIELDS = ("embedding", "embedding_model", "search_text")


def _clean(document) -> dict:
    data = serialize_doc(document)
    for field in HIDDEN_FIELDS:
        data.pop(field, None)
    return data


def build_job_query(
    search: str | None = None,
    prefecture: str | None = None,
    japanese: str | None = None,
    salary_min: int | None = None,
    skills: list[str] | None = None,
    remote: bool | None = None,
    company_id: str | None = None,
) -> dict:
    query: dict = {"is_active": True}

    keyword = normalize_search(search)
    if keyword:
        regex = contains(keyword)
        query["$or"] = [{"title": regex}, {"company_name": regex}, {"description": regex}]
    if prefecture:
        query["prefecture"] = prefecture
    if japanese:
        query["required_japanese"] = japanese
    if salary_min:
        # Tin không ghi lương vẫn hiện: lọc bỏ hẳn thì mất một phần ba số tin,
        # và "không ghi lương" không có nghĩa là "lương thấp".
        query["$and"] = [{"$or": [{"salary_max": {"$gte": salary_min}}, {"salary_max": None}]}]
    if skills:
        query["required_skills"] = {"$in": skills}
    if remote is not None:
        query["remote"] = remote
    if company_id:
        query["company"] = to_object_id(company_id, "company")

    return query


async def get_jobs(
    page: int = 1,
    search: str | None = None,
    prefecture: str | None = None,
    japanese: str | None = None,
    salary_min: int | None = None,
    skills: list[str] | None = None,
    remote: bool | None = None,
    company_id: str | None = None,
):
    query = build_job_query(search, prefecture, japanese, salary_min, skills, remote, company_id)

    total = await Job.find(query).count()
    jobs = await Job.find(query).sort("-crawled_at").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()

    # Một truy vấn cho toàn bộ công ty của cả trang, thay vì `Company.get()`
    # trong vòng lặp.
    company_map = await load_by_ids(Company, [j.company for j in jobs])

    items = []
    for job in jobs:
        data = _clean(job)
        company = company_map.get(str(job.company)) if job.company else None
        if company is not None:
            data["company"] = {
                "_id": str(company.id),
                "name": company.name,
                "logo_url": company.logo_url,
                "job_count": company.job_count,
            }
        items.append(data)

    return ok(
        jobs=items,
        totalPage=math.ceil(total / PAGE_SIZE) if total > 0 else 1,
        totalJobs=total,
        curPage=page,
    )


async def get_job_details(job_id: str):
    job = await Job.get(to_object_id(job_id, "job_id"))
    if not job:
        raise ApiError(404, code="job.notFound")

    data = _clean(job)
    if job.company:
        company = await Company.get(job.company)
        if company is not None:
            data["company"] = _clean(company)
    return ok(job=data)


async def get_companies(page: int = 1, search: str | None = None, with_profile: bool = False):
    query: dict = {}
    keyword = normalize_search(search)
    if keyword:
        query["name"] = contains(keyword)
    if with_profile:
        # Chỉ những công ty có mô tả thật (lấy từ trang hồ sơ doanh nghiệp).
        query["description"] = {"$ne": ""}

    total = await Company.find(query).count()
    companies = await Company.find(query).sort("-job_count").skip((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).to_list()

    return ok(
        companies=[_clean(c) for c in companies],
        totalPage=math.ceil(total / PAGE_SIZE) if total > 0 else 1,
        totalCompanies=total,
        curPage=page,
    )


async def get_company_details(company_id: str):
    company = await Company.get(to_object_id(company_id, "company_id"))
    if not company:
        raise ApiError(404, code="company.notFound")

    jobs = await Job.find({"company": company.id, "is_active": True}).limit(50).to_list()
    return ok(company=_clean(company), jobs=[_clean(j) for j in jobs])


async def get_job_filters():
    """Các giá trị đang thực sự có trong dữ liệu, để client dựng bộ lọc.

    Lấy từ DB chứ không viết cứng: nguồn thêm tỉnh mới hay công nghệ mới thì bộ
    lọc tự có, không phải sửa frontend.
    """
    prefectures = await Job.distinct("prefecture", {"is_active": True})
    japanese_levels = await Job.distinct("required_japanese", {"is_active": True})
    skills = await Job.aggregate(
        [
            {"$match": {"is_active": True}},
            {"$unwind": "$required_skills"},
            {"$group": {"_id": "$required_skills", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 40},
        ]
    ).to_list()

    return ok(
        prefectures=sorted(p for p in prefectures if p),
        japaneseLevels=[level for level in japanese_levels if level],
        skills=[{"name": s["_id"], "count": s["count"]} for s in skills],
    )
