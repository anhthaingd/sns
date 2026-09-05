"""Đưa tin tuyển dụng từ trang ngoài về DB dưới dạng có cấu trúc.

Trước khi có file này, chức năng crawl trả thẳng mảng HTML cho trình duyệt và
không lưu gì — không có dữ liệu để so khớp với CV, không tìm kiếm được, và mỗi
lần mở trang là phụ thuộc trang nguồn còn sống hay không.

Nguyên tắc quan trọng: **hỏng phải ồn ào**. Trang nguồn đổi giao diện thì
selector không khớp và parser trả về mảng rỗng — im lặng ghi 0 job trông y hệt
"hôm nay không có tin mới". Vì vậy nếu một nguồn trả 0 job trong khi DB đang có
tin của nguồn đó, ETL báo lỗi.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.models.company import Company
from app.models.job import Job
from app.services.browser import browser_service
from app.services.embedding import embed_texts, get_model_name
from app.services.etl.detail import enrich_from_detail
from app.services.etl.extract import (
    build_search_text,
    clean_text,
    is_remote,
    normalize_company_name,
    parse_employment_type,
    parse_language_level,
    parse_min_years,
    parse_prefecture,
    parse_salary,
)
from app.services.etl.parsers import SOURCES, nihongo
from app.services.etl.parsers.base import RawCompany, RawJob
from app.services.etl.skills import extract_skills
from app.services.job_index import bump_jobs_version
from app.utils.time import utc_now

logger = logging.getLogger("fuurin.etl")

# Mở tối đa vài trang cùng lúc; browser_service còn semaphore riêng của nó nên
# đây chỉ là lớp chặn thứ hai cho lịch sự với trang nguồn.
_PAGE_CONCURRENCY = 2

# Trang chi tiết tải từng tin một nên đây là phần chậm nhất của ETL.
_DETAIL_CONCURRENCY = 3

# Trần cho MỘT lần chạy để không giữ quá nhiều document trong RAM. Phần dư
# được báo ra log chứ không bỏ im lặng.
MAX_EMBED_PER_RUN = 2000


@dataclass
class SourceReport:
    source: str
    pages_fetched: int = 0
    jobs_parsed: int = 0
    jobs_enriched: int = 0
    jobs_embedded: int = 0
    jobs_written: int = 0
    companies_written: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class EtlReport:
    sources: list[SourceReport] = field(default_factory=list)
    started_at: datetime = field(default_factory=utc_now)
    finished_at: datetime | None = None

    @property
    def total_jobs(self) -> int:
        return sum(s.jobs_written for s in self.sources)

    @property
    def total_companies(self) -> int:
        return sum(s.companies_written for s in self.sources)

    @property
    def ok(self) -> bool:
        return all(s.ok for s in self.sources)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "totalJobs": self.total_jobs,
            "totalCompanies": self.total_companies,
            "startedAt": self.started_at.isoformat(),
            "finishedAt": self.finished_at.isoformat() if self.finished_at else None,
            "sources": [
                {
                    "source": s.source,
                    "pagesFetched": s.pages_fetched,
                    "jobsParsed": s.jobs_parsed,
                    "jobsEnriched": s.jobs_enriched,
                    "jobsEmbedded": s.jobs_embedded,
                    "jobsWritten": s.jobs_written,
                    "companiesWritten": s.companies_written,
                    "errors": s.errors,
                }
                for s in self.sources
            ],
        }


# ---------------------------------------------------------------------------
# Chuẩn hoá
# ---------------------------------------------------------------------------


def normalize_job(raw: RawJob) -> dict:
    """RawJob (toàn văn bản) -> các trường có kiểu của `Job`."""
    title = clean_text(raw.title)
    description = clean_text(raw.description)
    # Trích kỹ năng trên text ĐÃ LÀM SẠCH: nhãn trang trí lặp lại ở mọi thẻ
    # ("直接採用", "NEW", "HOT") vừa gây khớp nhầm vừa làm loãng tín hiệu.
    skills = extract_skills(title, description, clean_text(raw.raw_text))
    salary_min, salary_max = parse_salary(raw.salary_text)
    work_context = raw.employment_text or raw.raw_text

    return {
        "source": raw.source,
        "source_id": raw.source_id,
        "url": raw.url,
        "title": title,
        "company_name": raw.company_name.strip(),
        "location": clean_text(raw.location_text) or None,
        "prefecture": parse_prefecture(raw.location_text),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "employment_type": parse_employment_type(work_context),
        "remote": is_remote(work_context),
        "description": description,
        "required_skills": skills,
        "required_japanese": parse_language_level(raw.japanese_text),
        "required_english": parse_language_level(raw.english_text),
        "min_years": parse_min_years(raw.raw_text),
        "search_text": build_search_text(title, raw.company_name, skills, description),
        "crawled_at": utc_now(),
        "is_active": True,
    }


async def upsert_company(name: str, source: str, profile: RawCompany | None = None) -> Company | None:
    """Tạo hoặc cập nhật công ty theo tên đã chuẩn hoá.

    Cập nhật chứ không ghi đè: một nguồn chỉ có tên công ty không được phép xoá
    mất phần mô tả mà nguồn khác đã lấy được.
    """
    key = normalize_company_name(profile.name if profile else name)
    if not key:
        return None

    company = await Company.find_one(Company.name_normalized == key)
    if company is None:
        company = Company(name=(profile.name if profile else name).strip(), name_normalized=key)

    if source not in company.sources:
        company.sources.append(source)

    if profile is not None:
        company.profile_source = profile.source
        company.profile_source_id = profile.source_id
        company.profile_url = profile.url
        company.website = profile.website or company.website
        company.logo_url = profile.logo_url or company.logo_url
        company.location = profile.location or company.location
        company.prefecture = parse_prefecture(profile.location) or company.prefecture
        company.description = profile.description or company.description
        company.job_count = profile.job_count or company.job_count
        company.tech_stack = extract_skills(profile.description) or company.tech_stack

    company.search_text = build_search_text(company.name, "", company.tech_stack, company.description)
    company.crawled_at = utc_now()
    await company.save()
    return company


# ---------------------------------------------------------------------------
# Chạy ETL
# ---------------------------------------------------------------------------


async def _fetch_page(source: str, page: int) -> str:
    url = SOURCES[source]["list_url"](page)
    logger.info("ETL %s trang %s: %s", source, page, url)
    html, _css = await browser_service.fetch_page(url)
    return html


# Trang danh sách và trang chi tiết mạnh yếu khác nhau, nên gộp theo từng
# trường chứ không theo một quy tắc chung:
#
# - `required_japanese`/`required_english`: trang danh sách của GaijinPot có
#   trường CÓ CẤU TRÚC, đáng tin hơn phép dò trong văn bản -> giữ nếu đã có.
# - `description`/`required_skills`: trang chi tiết luôn đầy đủ hơn -> lấy bản
#   giàu hơn. Quy tắc "chỉ điền vào chỗ trống" từng khiến mô tả 1.500 ký tự bị
#   bỏ qua chỉ vì thẻ danh sách đã có sẵn 100 ký tự.
_PREFER_LIST_PAGE = ("required_japanese", "required_english")
_PREFER_RICHER = ("description", "required_skills")


def _merge_detail(data: dict, extra: dict) -> dict:
    for key, value in extra.items():
        if not value:
            continue
        if key in _PREFER_LIST_PAGE:
            data.setdefault(key, None)
            if not data[key]:
                data[key] = value
        elif key in _PREFER_RICHER:
            if len(value) > len(data.get(key) or ""):
                data[key] = value
        elif not data.get(key):
            data[key] = value

    data["search_text"] = build_search_text(
        data["title"], data["company_name"], data["required_skills"], data["description"]
    )
    return data


async def write_job(raw: RawJob, company: Company | None, extra: dict | None = None) -> bool:
    data = normalize_job(raw)
    if extra:
        data = _merge_detail(data, extra)
    if company is not None:
        data["company"] = company.id

    existing = await Job.find_one({"source": raw.source, "source_id": raw.source_id})
    if existing is None:
        await Job(**data).insert()
        return True

    for key, value in data.items():
        setattr(existing, key, value)
    await existing.save()
    return True


async def _enrich_jobs(raw_jobs: list[RawJob], report: SourceReport, limit: int) -> dict[str, dict]:
    """Tải trang chi tiết cho tối đa `limit` tin, trả về map source_id -> trường thêm."""
    targets = [raw for raw in raw_jobs if raw.url][:limit]
    extra: dict[str, dict] = {}
    semaphore = asyncio.Semaphore(_DETAIL_CONCURRENCY)

    async def one(raw: RawJob) -> None:
        async with semaphore:
            try:
                html, _ = await browser_service.fetch_page(raw.url)
            except Exception as err:
                # Một tin lỗi không được làm hỏng cả mẻ: tin vẫn ghi được với
                # dữ liệu từ trang danh sách.
                logger.warning("Không tải được chi tiết %s: %s", raw.url, err)
                return
            fields = enrich_from_detail(html)
            if fields:
                extra[raw.source_id] = fields

    await asyncio.gather(*(one(raw) for raw in targets))
    report.jobs_enriched = len(extra)
    return extra


async def run_source(source: str, pages: int, with_companies: bool = True, detail_limit: int = 0) -> SourceReport:
    report = SourceReport(source=source)
    parse = SOURCES[source]["parse"]

    raw_jobs: list[RawJob] = []
    semaphore = asyncio.Semaphore(_PAGE_CONCURRENCY)

    async def fetch_and_parse(page: int) -> None:
        async with semaphore:
            try:
                html = await _fetch_page(source, page)
            except Exception as err:  # trang nguồn timeout / chặn
                report.errors.append(f"trang {page}: {type(err).__name__}: {err}")
                return
            report.pages_fetched += 1
            raw_jobs.extend(parse(html))

    await asyncio.gather(*(fetch_and_parse(p) for p in range(1, pages + 1)))
    report.jobs_parsed = len(raw_jobs)

    # Chốt chặn "hỏng ồn ào": lấy được trang nhưng không ra tin nào, trong khi
    # DB đang có tin cũ của nguồn này -> selector đã mục rữa.
    if report.pages_fetched and not raw_jobs:
        existing = await Job.find({"source": source}).count()
        message = f"{source}: tải được {report.pages_fetched} trang nhưng parse ra 0 tin"
        if existing:
            report.errors.append(f"{message} (DB đang có {existing} tin) — selector có thể đã lỗi thời")
            logger.error(report.errors[-1])
        else:
            logger.warning(message)

    # Hồ sơ công ty đầy đủ: hiện chỉ nihongo-engineer có trang riêng.
    profiles: dict[str, RawCompany] = {}
    if with_companies and source == nihongo.SOURCE:
        profiles = await _fetch_nihongo_companies(raw_jobs, report, pages)

    detail_fields: dict[str, dict] = {}
    if detail_limit:
        detail_fields = await _enrich_jobs(raw_jobs, report, detail_limit)

    companies_seen: set[str] = set()

    # Ghi trước mọi hồ sơ lấy được, kể cả công ty chưa có tin nào trong trang
    # đã crawl — đây chính là dữ liệu để trả lời "công ty A cần gì".
    for profile in profiles.values():
        company = await upsert_company(profile.name, source, profile)
        if company is not None and company.name_normalized not in companies_seen:
            companies_seen.add(company.name_normalized)
            report.companies_written += 1

    for raw in raw_jobs:
        profile = profiles.get(raw.company_source_id) if raw.company_source_id else None
        company = await upsert_company(raw.company_name, source, profile)
        if company is not None and company.name_normalized not in companies_seen:
            companies_seen.add(company.name_normalized)
            report.companies_written += 1
        if await write_job(raw, company, detail_fields.get(raw.source_id)):
            report.jobs_written += 1

    return report


async def _fetch_nihongo_companies(raw_jobs: list[RawJob], report: SourceReport, pages: int) -> dict[str, RawCompany]:
    # Gộp hai nguồn id: công ty được nhắc trong tin, VÀ trang danh sách công ty.
    # Chỉ dựa vào tin thì gần như chỉ lấy được một hồ sơ, vì trang chủ việc làm
    # bị một công ty môi giới chiếm gần hết.
    ids = {raw.company_source_id for raw in raw_jobs if raw.company_source_id}
    for page in range(1, pages + 1):
        try:
            html, _ = await browser_service.fetch_page(nihongo.company_list_url(page))
        except Exception as err:
            report.errors.append(f"danh sách công ty trang {page}: {type(err).__name__}: {err}")
            break
        found = nihongo.parse_company_ids(html)
        if not found:
            break
        ids.update(found)
    profiles: dict[str, RawCompany] = {}
    for company_id in sorted(ids):
        try:
            html, _ = await browser_service.fetch_page(nihongo.company_url(company_id))
        except Exception as err:
            report.errors.append(f"hồ sơ công ty {company_id}: {type(err).__name__}: {err}")
            continue
        profile = nihongo.parse_company(html, company_id)
        if profile is not None:
            profiles[company_id] = profile
    return profiles


async def run_etl(
    sources: list[str] | None = None,
    pages: int = 5,
    with_companies: bool = True,
    detail_limit: int = 0,
    with_embeddings: bool = True,
) -> EtlReport:
    selected = sources or list(SOURCES)
    unknown = [s for s in selected if s not in SOURCES]
    if unknown:
        raise ValueError(f"Nguồn không tồn tại: {unknown}. Có: {sorted(SOURCES)}")

    report = EtlReport()
    for source in selected:
        try:
            report.sources.append(await run_source(source, pages, with_companies, detail_limit))
        except Exception as err:
            logger.exception("ETL %s hỏng", source)
            report.sources.append(SourceReport(source=source, errors=[f"{type(err).__name__}: {err}"]))

    # Số vị trí đang tuyển: nguồn nào không nói thì tự đếm từ chính DB.
    await _recount_company_jobs()

    if with_embeddings:
        embedded = await embed_pending()
        if report.sources:
            report.sources[-1].jobs_embedded = embedded

    # Báo cho mọi worker biết chỉ mục vector đã cũ.
    await bump_jobs_version()

    report.finished_at = utc_now()
    return report


async def embed_pending(batch_size: int = 128) -> int:
    """Tính vector cho tin và công ty chưa có, hoặc có vector của model cũ.

    Chạy sau khi ghi xong dữ liệu chứ không xen vào giữa: nếu embedder chết thì
    dữ liệu vẫn nằm đủ trong DB, chỉ thiếu phần xếp hạng theo ngữ nghĩa — chạy
    lại bước này sau là đủ, không phải crawl lại từ đầu.
    """
    embedded = 0
    for model in (Job, Company):
        pending = (
            await model.find(
                {"search_text": {"$ne": ""}, "embedding": None},
            )
            .limit(batch_size * 20)
            .to_list()
        )

        for start in range(0, len(pending), batch_size):
            chunk = pending[start : start + batch_size]
            vectors = await embed_texts([doc.search_text for doc in chunk])
            if vectors is None:
                logger.warning("Embedder không dùng được — bỏ qua bước tính vector")
                return embedded
            model_name = get_model_name()
            for doc, vector in zip(chunk, vectors, strict=True):
                doc.embedding = vector
                doc.embedding_model = model_name
                await doc.save()
            embedded += len(chunk)

    return embedded


async def _recount_company_jobs() -> None:
    pipeline = [
        {"$match": {"company": {"$ne": None}, "is_active": True}},
        {"$group": {"_id": "$company", "count": {"$sum": 1}}},
    ]
    async for row in Job.aggregate(pipeline):
        company = await Company.get(row["_id"])
        # Nguồn có nói số vị trí (nihongo: "129 open jobs") thì tin nguồn hơn,
        # vì ETL chỉ crawl vài trang đầu nên đếm được ít hơn thực tế.
        if company is not None and not company.job_count:
            company.job_count = row["count"]
            await company.save()
