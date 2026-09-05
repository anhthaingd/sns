"""Sinh CV mẫu đa dạng để kiểm chứng chức năng gợi ý công ty.

    docker compose run --rm server python -m scripts.seed_resumes --count 100
    docker compose run --rm server python -m scripts.seed_resumes --clean

Vì sao cần: DB thật chỉ có 6 CV và **không CV nào có kinh nghiệm làm việc**.
Với dữ liệu đó thì mọi hồ sơ đều ra một danh sách gợi ý giống nhau, và không có
cách nào chứng minh phần so khớp thật sự hoạt động.

Các hồ sơ được dựng để ĐỐI LẬP NHAU một cách có chủ đích — cùng ngành nhưng
khác trình độ tiếng Nhật, cùng trình độ nhưng khác ngành — để nhìn vào kết quả
là thấy ngay hệ thống có phân biệt được hay không.

Dùng seed cố định nên chạy lại cho ra đúng cùng bộ dữ liệu.
"""

import argparse
import asyncio
import itertools
import logging
import random
import sys

import bcrypt
from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.models.follower import Follower
from app.models.following import Following
from app.models.resume import Resume
from app.models.role import Role
from app.models.user import User
from app.services.embedding import close_embedder, embed_texts, get_model_name
from app.services.resume_profile import apply_profile, resume_text, text_hash

logger = logging.getLogger("fuurin.seed")

# Email theo khuôn này để `--clean` xoá đúng dữ liệu mẫu, không đụng tài khoản thật.
SEED_EMAIL_DOMAIN = "seed.fuurin.local"

# Mỗi nghề: chức danh + bộ kỹ năng thường gặp trong tin thật của bốn nguồn.
PROFESSIONS = [
    ("Backend Engineer", ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"], "IT"),
    ("Backend Engineer", ["Java", "Spring Boot", "MySQL", "Kubernetes"], "IT"),
    ("Backend Engineer", ["Go", "gRPC", "MongoDB", "Microservices"], "IT"),
    ("Frontend Engineer", ["React", "TypeScript", "Next.js", "Tailwind CSS"], "IT"),
    ("Frontend Engineer", ["Vue.js", "JavaScript", "Sass", "Webpack"], "IT"),
    ("Full Stack Engineer", ["Node.js", "React", "PostgreSQL", "AWS"], "IT"),
    ("Mobile Engineer", ["Flutter", "Dart", "Firebase"], "IT"),
    ("Mobile Engineer", ["Kotlin", "Android", "Swift", "iOS"], "IT"),
    ("DevOps Engineer", ["Kubernetes", "Terraform", "AWS", "CI/CD", "Prometheus"], "IT"),
    ("Data Engineer", ["Python", "Spark", "Airflow", "BigQuery", "SQL"], "IT"),
    ("Machine Learning Engineer", ["Python", "PyTorch", "Machine Learning", "NLP"], "IT"),
    ("QA Engineer", ["Selenium", "Playwright", "Pytest", "Testing"], "IT"),
    ("English Teacher", ["Teaching", "Translation"], "EDU"),
    ("Sales Manager", ["Sales", "Marketing", "Project Management"], "BIZ"),
    ("Customer Support", ["Customer Support", "Translation"], "BIZ"),
    ("UI/UX Designer", ["Figma", "UI/UX", "Adobe XD"], "DESIGN"),
]

# Trình độ tiếng Nhật viết đúng như người dùng thật hay gõ vào ô Languages.
JAPANESE_VARIANTS = [
    ("Japanese N1", "fluent"),
    ("Japanese N2", "business"),
    ("Japanese N3", "conversational"),
    ("Japanese N5", "basic"),
    ("Japanese (no certificate)", "conversational"),
    (None, None),
]
ENGLISH_VARIANTS = ["English (Native level)", "English business level", "English conversational", None]

EXPERIENCE_YEARS = [0, 1, 3, 6, 10]

CITIES = ["Tokyo", "Osaka", "Fukuoka", "Kanagawa", "Kyoto"]


def _experiences(rng: random.Random, years: int, position: str) -> list[dict]:
    if years == 0:
        return []
    end = 2026
    start = end - years
    return [
        {
            "name": rng.choice(["Rakuten", "CyberAgent", "FPT Japan", "NTT Data", "Freelance"]),
            "startTime": f"{start}-04",
            "endTime": f"{end}-03",
            "position": position,
            "description": f"{position} với {years} năm kinh nghiệm, tham gia phát triển và vận hành hệ thống.",
        }
    ]


def build_profiles(count: int, seed: int = 20260905) -> list[dict]:
    rng = random.Random(seed)
    # Nhân chéo nghề × tiếng Nhật × số năm để chắc chắn phủ đủ các thái cực,
    # thay vì bốc ngẫu nhiên rồi hên xui thiếu mất một nhóm.
    combos = list(itertools.product(PROFESSIONS, JAPANESE_VARIANTS, EXPERIENCE_YEARS))
    rng.shuffle(combos)

    profiles = []
    for index, ((position, skills, field), (jp_text, _), years) in enumerate(combos[:count]):
        english = rng.choice(ENGLISH_VARIANTS)
        languages = [t for t in (jp_text, english) if t]
        profiles.append(
            {
                "index": index,
                "position": position,
                "skills": skills,
                "field": field,
                "languages": languages,
                "years": years,
                "city": rng.choice(CITIES),
                "salary": rng.choice([3_000_000, 4_000_000, 5_000_000, 7_000_000, 9_000_000]),
            }
        )
    return profiles


async def _seed_user(profile: dict, role_id, password_hash: str) -> User:
    email = f"seed-{profile['index']:03d}@{SEED_EMAIL_DOMAIN}"
    existing = await User.find_one(User.email == email)
    if existing:
        return existing

    user = User(
        email=email,
        password=password_hash,
        username=f"{profile['position']} #{profile['index']:03d}",
        address=profile["city"],
        role=role_id,
    )
    await user.insert()
    await Follower(user=user.id).insert()
    await Following(user=user.id).insert()
    return user


async def seed(count: int) -> dict:
    role = await Role.find_one(Role.value == 0)
    # Băm một lần rồi dùng lại: bcrypt cố ý chậm, băm 100 lần mất vài chục giây.
    password_hash = bcrypt.hashpw(b"SeedPassw0rd!", bcrypt.gensalt(10)).decode("utf-8")

    created = 0
    resumes: list[Resume] = []

    for profile in build_profiles(count):
        user = await _seed_user(profile, role.id if role else None, password_hash)
        resume = await Resume.find_one(Resume.user == user.id)
        if resume is None:
            resume = Resume(user=user.id)
            created += 1

        resume.name = user.username
        resume.position = profile["position"]
        resume.email = user.email
        resume.address = profile["city"]
        resume.objective = f"Tìm vị trí {profile['position']} tại Nhật Bản."
        resume.skills = list(profile["skills"])
        resume.languages = list(profile["languages"])
        resume.experiences = _experiences(random.Random(profile["index"]), profile["years"], profile["position"])
        resume.desired_salary_min = profile["salary"]
        resume.desired_locations = [profile["city"]]

        # Đi qua đúng hàm mà ứng dụng thật dùng, để dữ liệu mẫu không "đẹp hơn"
        # dữ liệu thật một cách giả tạo.
        apply_profile(resume, overwrite=True)
        await resume.save()
        resumes.append(resume)

    vectors = await embed_texts([resume_text(r) for r in resumes])
    embedded = 0
    if vectors is None:
        logger.warning("Embedder không dùng được — CV mẫu chưa có vector, chạy lại sau bằng backfill_resumes")
    else:
        model = get_model_name()
        for resume, vector in zip(resumes, vectors, strict=True):
            resume.embedding = vector
            resume.embedding_model = model
            resume.embedding_source_hash = text_hash(resume_text(resume))
            await resume.save()
            embedded += 1

    return {"users_created": created, "resumes": len(resumes), "embedded": embedded}


async def clean() -> dict:
    users = await User.find({"email": {"$regex": f"@{SEED_EMAIL_DOMAIN}$"}}).to_list()
    ids = [u.id for u in users]
    if not ids:
        return {"users": 0, "resumes": 0}

    resumes = await Resume.find({"user": {"$in": ids}}).delete()
    await Follower.find({"user": {"$in": ids}}).delete()
    await Following.find({"user": {"$in": ids}}).delete()
    await User.find({"_id": {"$in": ids}}).delete()
    return {"users": len(ids), "resumes": resumes.deleted_count if resumes else 0}


async def main() -> int:
    parser = argparse.ArgumentParser(description="Sinh CV mau da dang de test chuc nang goi y")
    parser.add_argument("--count", type=int, default=100, help="So CV can sinh (mac dinh 100)")
    parser.add_argument("--clean", action="store_true", help="Xoa toan bo du lieu mau")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await connect_db()
    await connect_redis()
    try:
        result = await clean() if args.clean else await seed(args.count)
    finally:
        await close_embedder()
        await close_redis()
        await close_db()

    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
