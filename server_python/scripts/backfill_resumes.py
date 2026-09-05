"""Điền các trường mới cho CV đã có trong DB, suy ra từ dữ liệu cũ.

    docker compose run --rm server python -m scripts.backfill_resumes
    docker compose run --rm server python -m scripts.backfill_resumes --overwrite

CV cũ chỉ có `languages: ["JP", "EN"]` (không trình độ) và `skills` do người
dùng tự gõ. Chức năng gợi ý công ty cần trình độ tiếng Nhật, số năm kinh nghiệm
và kỹ năng đã chuẩn hoá. Script này suy ra bằng LUẬT — không cần LLM, không cần
bắt người dùng nhập lại.

Mặc định chỉ điền vào chỗ đang trống; `--overwrite` mới ghi đè.
"""

import argparse
import asyncio
import logging
import sys

from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.models.resume import Resume
from app.services.embedding import close_embedder, embed_texts, get_model_name
from app.services.resume_profile import apply_profile, resume_text, text_hash

logger = logging.getLogger("fuurin.backfill")


async def backfill(overwrite: bool) -> dict:
    resumes = await Resume.find_all().to_list()
    updated = 0
    embedded = 0

    for resume in resumes:
        before = (
            resume.japanese_level,
            resume.english_level,
            resume.years_of_experience,
            tuple(resume.skills_normalized or []),
        )
        apply_profile(resume, overwrite=overwrite)
        after = (
            resume.japanese_level,
            resume.english_level,
            resume.years_of_experience,
            tuple(resume.skills_normalized or []),
        )
        if before != after:
            updated += 1
            await resume.save()

    # Tính vector sau khi đã có `skills_normalized`, nếu không thì vector thiếu
    # đúng phần quan trọng nhất.
    pending = [r for r in resumes if r.embedding is None or r.embedding_source_hash != text_hash(resume_text(r))]
    if pending:
        vectors = await embed_texts([resume_text(r) for r in pending])
        if vectors is None:
            logger.warning("Embedder không dùng được — bỏ qua bước tính vector cho CV")
        else:
            model = get_model_name()
            for resume, vector in zip(pending, vectors, strict=True):
                resume.embedding = vector
                resume.embedding_model = model
                resume.embedding_source_hash = text_hash(resume_text(resume))
                await resume.save()
                embedded += 1

    return {"total": len(resumes), "updated": updated, "embedded": embedded}


async def main() -> int:
    parser = argparse.ArgumentParser(description="Dien truong moi cho CV da co")
    parser.add_argument("--overwrite", action="store_true", help="Ghi de ca gia tri nguoi dung da nhap")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await connect_db()
    await connect_redis()
    try:
        result = await backfill(args.overwrite)
    finally:
        await close_embedder()
        await close_redis()
        await close_db()

    print(f"CV: {result['total']} | da dien them: {result['updated']} | da tinh vector: {result['embedded']}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
