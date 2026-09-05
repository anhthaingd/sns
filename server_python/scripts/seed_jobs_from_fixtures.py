"""Nạp việc làm & doanh nghiệp từ HTML đã lưu trong `tests/fixtures/`.

    docker compose run --rm server python -m scripts.seed_jobs_from_fixtures

Vì sao cần: sau `docker compose up` lần đầu, collection `jobs` rỗng nên trang
việc làm và chức năng gợi ý trông như hỏng. Chạy ETL thật thì cần internet, mất
vài phút, và phụ thuộc bốn trang nguồn còn sống hay không — không phù hợp cho
lần chạy đầu tiên và cho CI.

Script này đi qua ĐÚNG parser và ĐÚNG bước chuẩn hoá mà ETL thật dùng, chỉ khác
nguồn HTML là file thay vì mạng. Nhờ vậy dữ liệu mẫu không "đẹp hơn" dữ liệu
thật một cách giả tạo, và nếu parser hỏng thì hỏng ở cả hai đường.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.models.company import Company
from app.models.job import Job
from app.services.embedding import close_embedder
from app.services.etl.parsers import SOURCES, nihongo
from app.services.etl.pipeline import embed_pending, upsert_company, write_job
from app.services.job_index import bump_jobs_version

logger = logging.getLogger("fuurin.seed_jobs")

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


async def seed(with_embeddings: bool = True) -> dict:
    profiles = {}
    company_page = FIXTURES / "nihongo_company.html"
    if company_page.exists():
        profile = nihongo.parse_company(company_page.read_text(encoding="utf-8"), "2")
        if profile is not None:
            profiles[profile.source_id] = profile

    written = 0
    companies: set[str] = set()

    for source in sorted(SOURCES):
        fixture = FIXTURES / f"{source}.html"
        if not fixture.exists():
            logger.warning("Không có fixture cho %s, bỏ qua", source)
            continue

        for raw in SOURCES[source]["parse"](fixture.read_text(encoding="utf-8")):
            profile = profiles.get(raw.company_source_id) if raw.company_source_id else None
            company = await upsert_company(raw.company_name, source, profile)
            if company is not None:
                companies.add(company.name_normalized)
            await write_job(raw, company)
            written += 1

    embedded = await embed_pending() if with_embeddings else 0
    await bump_jobs_version()

    return {
        "jobs_written": written,
        "companies": len(companies),
        "embedded": embedded,
        "jobs_total": await Job.find_all().count(),
        "companies_total": await Company.find_all().count(),
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Nap du lieu viec lam mau tu fixture (khong can mang)")
    parser.add_argument("--no-embed", action="store_true", help="Bo qua buoc tinh vector")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await connect_db()
    await connect_redis()
    try:
        result = await seed(with_embeddings=not args.no_embed)
    finally:
        await close_embedder()
        await close_redis()
        await close_db()

    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
