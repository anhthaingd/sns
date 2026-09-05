"""Chạy ETL: crawl tin tuyển dụng -> chuẩn hoá -> ghi vào MongoDB.

    docker compose run --rm server python -m scripts.run_etl --pages 5
    docker compose run --rm server python -m scripts.run_etl --source gaijinpot daijob --pages 10
    docker compose run --rm server python -m scripts.run_etl --pages 3 --no-companies

Chạy lại nhiều lần an toàn: mỗi tin ghi theo khoá (source, source_id) nên cập
nhật bản ghi cũ chứ không nhân bản.
"""

import argparse
import asyncio
import json
import logging
import sys

from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.services.browser import browser_service
from app.services.embedding import close_embedder
from app.services.etl.parsers import SOURCES
from app.services.etl.pipeline import embed_pending, run_etl
from app.services.job_index import bump_jobs_version


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl và chuẩn hoá tin tuyển dụng")
    parser.add_argument(
        "--source",
        nargs="+",
        choices=sorted(SOURCES),
        help="Nguồn cần crawl (mặc định: tất cả)",
    )
    parser.add_argument("--pages", type=int, default=5, help="Số trang mỗi nguồn (mặc định 5)")
    parser.add_argument(
        "--detail",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Tai them trang chi tiet cho toi da N tin moi nguon de lay yeu cau "
            "tieng Nhat, ky nang, so nam kinh nghiem. Cham hon nhieu (moi tin mot "
            "luot tai trang) nhung du lieu day du hon han."
        ),
    )
    parser.add_argument(
        "--embed-only",
        action="store_true",
        help=(
            "Khong crawl, chi tinh vector cho tin/cong ty dang thieu. Dung khi "
            "embedder vua san sang hoac vua doi model."
        ),
    )
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="Bo qua buoc tinh vector (dung khi service embedder chua san sang)",
    )
    parser.add_argument(
        "--no-companies",
        action="store_true",
        help="Bỏ qua việc tải trang hồ sơ doanh nghiệp (nhanh hơn nhiều)",
    )
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    await connect_db()
    await connect_redis()
    try:
        if args.embed_only:
            embedded = await embed_pending()
            await bump_jobs_version()
            print(f"Da tinh vector cho {embedded} ban ghi")
            return 0

        report = await run_etl(
            sources=args.source,
            pages=args.pages,
            with_companies=not args.no_companies,
            detail_limit=args.detail,
            with_embeddings=not args.no_embed,
        )
    finally:
        await browser_service.stop()
        await close_embedder()
        await close_redis()
        await close_db()

    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

    for source in report.sources:
        status = "OK  " if source.ok else "LOI "
        print(
            f"{status} {source.source:<11} {source.jobs_written:>4} tin"
            f"  {source.jobs_enriched:>3} lam giau"
            f"  {source.jobs_embedded:>4} vector"
            f"  {source.companies_written:>3} công ty" + (f"  <- {'; '.join(source.errors)}" if source.errors else ""),
            file=sys.stderr,
        )

    # Mã thoát khác 0 khi có nguồn hỏng để CI/cron bắt được.
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
