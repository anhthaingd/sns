"""Tạo tài khoản DEMO kèm CV đầy đủ để trình diễn chức năng gợi ý công ty.

    docker compose run --rm server python -m scripts.seed_demo_user
    docker compose run --rm server python -m scripts.seed_demo_user --contrast
    docker compose run --rm server python -m scripts.seed_demo_user --clean

Khác với `scripts/seed_resumes.py` (sinh 100 CV rút gọn để KIỂM CHỨNG rằng phần
so khớp phân biệt được các hồ sơ khác nhau), file này tạo ĐÚNG MỘT hồ sơ được
viết tay đầy đủ mọi mục để ĐEM ĐI TRÌNH BÀY: mở trang CV lên không có ô nào
trống, và hai chức năng AI đều có nội dung thật để nói.

CV này CỐ Ý KHÔNG HOÀN HẢO
--------------------------
Đây là quyết định thiết kế quan trọng nhất của file này. Một CV hoàn hảo sẽ làm
hỏng buổi demo: chức năng "còn thiếu gì để vào công ty A" sẽ không có gì để
hiển thị. Hồ sơ dưới đây được dựng để mỗi loại khoảng cách đều xuất hiện ít
nhất một lần trên dữ liệu thật:

    tiếng Nhật N3   -> tin đòi N2/N1 hiện rào cản ngôn ngữ (chặn)
    4 năm kinh nghiệm -> tin đòi 5 năm trở lên hiện thiếu số năm (chặn)
    không có Kubernetes/Terraform/Go -> tin DevOps hiện thiếu kỹ năng
    mong muốn Tokyo -> tin ở tỉnh khác hiện ghi chú địa điểm (không chặn)
    mong muốn 5 triệu yên/năm -> tin trả thấp hơn hiện ghi chú lương (không chặn)

Đồng thời hồ sơ vẫn đủ mạnh để đứng đầu bảng ở nhóm việc Backend — nếu không
thì demo chỉ toàn màu đỏ và cũng không thuyết phục.

Chạy lại nhiều lần cho ra đúng một kết quả: tìm theo email, có thì cập nhật,
chưa có thì tạo. Dữ liệu đi qua đúng `apply_profile` / `resume_text` mà ứng
dụng thật dùng lúc người dùng bấm Lưu CV, nên hồ sơ demo không "đẹp hơn" hồ sơ
thật một cách giả tạo.
"""

import argparse
import asyncio
import logging
import sys

import bcrypt
from app.config.database import close_db, connect_db
from app.config.redis_client import close_redis, connect_redis
from app.config.settings import UPLOAD_ROOT
from app.models.follower import Follower
from app.models.following import Following
from app.models.job import Job, JobMatchView
from app.models.resume import Resume
from app.models.role import Role
from app.models.user import User
from app.services.embedding import close_embedder, embed_texts, get_model_name
from app.services.job_index import job_index
from app.services.matching import evaluate
from app.services.resume_profile import apply_profile, resume_text, text_hash

logger = logging.getLogger("fuurin.seed_demo")

DEMO_PASSWORD = "Demo@12345"

# Thư mục chứng chỉ do `app/main.py` mount ở /public, client ghép thành
# `${VITE_BACKEND_URL}/${url}`. Sinh file thật ở đây để link tải trong trang CV
# bấm được — demo mà bấm vào ra 404 thì mất điểm.
CERTIFICATE_DIR = UPLOAD_ROOT / "certificates"
CERTIFICATE_PREFIX = "demo-fuurin-"


# --- Nội dung CV ---------------------------------------------------------
# Mốc thời gian để cứng (không lấy ngày hiện tại) để chạy lại lúc nào cũng ra
# đúng 4 năm kinh nghiệm — con số này được nhắc trong kịch bản demo.
DEMO_RESUME = {
    "name": "Trần Minh Quân",
    "position": "Backend Engineer",
    "birthday": "1998-06-14",
    "phone": "090-1234-5678",
    "address": "Tokyo",
    "github": "https://github.com/quan-tran-demo",
    # Không nhắc tới tiếng Nhật ở đây, cũng như trong mục kinh nghiệm và dự án.
    # Lý do ở phần chú thích của CONTRAST_ACCOUNT — đây là điều kiện để phép so
    # sánh giữa hai tài khoản demo có giá trị.
    "objective": (
        "Kỹ sư Backend 4 năm kinh nghiệm với Python, FastAPI và Django, "
        "quen thiết kế REST API, tối ưu PostgreSQL và vận hành dịch vụ trên Docker. "
        "Mong muốn làm việc dài hạn tại Tokyo trong đội phát triển sản phẩm."
    ),
    "educationName": "Đại học Bách khoa Hà Nội",
    "educationMajor": "Công nghệ thông tin",
    "educationCompletion": "2020-06",
    "educationGPA": "3.42 / 4.0",
    # Chỉ liệt kê kỹ năng THẬT SỰ có. Cố ý không có Kubernetes, Terraform, Go,
    # TypeScript — đó là phần "còn thiếu" mà chức năng 2 sẽ chỉ ra.
    "skills": [
        "Python",
        "FastAPI",
        "Django",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Docker",
        "Nginx",
        "Linux",
        "Git",
        "REST API",
        "SQL",
        "Pytest",
        "CI/CD",
        "AWS",
    ],
    "languages": [
        "Japanese N3 (JLPT)",
        "English - business level (TOEIC 850)",
        "Vietnamese - native",
    ],
    # Tổng cộng đúng 4 năm (2022->2024 và 2024->2026) để số năm tự suy ra khớp
    # với số năm tự khai; lệch nhau thì người xem sẽ hỏi ngay.
    "experiences": [
        {
            "name": "FPT Software Japan",
            "startTime": "2022-04",
            "endTime": "2024-03",
            "position": "Backend Developer",
            "description": (
                "Phát triển REST API bằng Django cho hệ thống quản lý kho hàng. "
                "Viết truy vấn và đánh index PostgreSQL, giảm thời gian phản hồi trang danh sách "
                "từ 2.4 giây xuống 380ms. Chuẩn hoá tài liệu API và quy trình review code cho nhóm 6 người."
            ),
        },
        {
            "name": "Rakuten Group",
            "startTime": "2024-04",
            "endTime": "2026-09",
            "position": "Backend Engineer",
            "description": (
                "Xây dựng dịch vụ thanh toán nội bộ bằng Python và FastAPI, xử lý khoảng 120 "
                "yêu cầu mỗi giây. Dùng Redis làm hàng đợi và bộ nhớ đệm, đóng gói bằng Docker, "
                "triển khai qua CI/CD trên AWS. Phụ trách viết test với Pytest cho toàn đội."
            ),
        },
    ],
    "projects": [
        {
            "name": "Hệ thống đặt lịch khám trực tuyến",
            "tech": "Python, FastAPI, PostgreSQL, Redis, Docker",
            "description": (
                "Dịch vụ đặt lịch cho 3 phòng khám tại Tokyo, có xác thực JWT, phân quyền "
                "theo vai trò và gửi nhắc lịch tự động. Tự thiết kế cơ sở dữ liệu và viết "
                "tài liệu API."
            ),
        },
        {
            "name": "Công cụ đối soát giao dịch nội bộ",
            "tech": "Python, Django, MySQL, Nginx",
            "description": (
                "Tự động đối chiếu giao dịch giữa hai hệ thống kế toán, thay cho quy trình "
                "làm tay mất 6 giờ mỗi tuần. Xuất báo cáo chênh lệch và cảnh báo qua email."
            ),
        },
    ],
    # (tên hiển thị, nội dung in trong file PDF sinh kèm)
    "certificates": [
        ("JLPT N3 - 2024/12", ["JLPT N3", "Japanese Language Proficiency Test", "Issued: December 2024"]),
        ("TOEIC 850 - 2025/03", ["TOEIC Listening & Reading", "Score: 850 / 990", "Issued: March 2025"]),
        (
            "AWS Certified Solutions Architect - Associate",
            ["AWS Certified Solutions Architect", "Associate level", "Issued: August 2025"],
        ),
    ],
    # Người dùng tự khai ở mục "Mục tiêu nghề nghiệp" trên form CV.
    "japanese_level": "conversational",
    "english_level": "business",
    "years_of_experience": 4,
    "desired_salary_min": 5_000_000,
    "desired_locations": ["Tokyo"],
}

DEMO_EMAIL = "demo@fuurin.local"
CONTRAST_EMAIL = "demo-nojp@fuurin.local"

DEMO_ACCOUNT = {
    "email": DEMO_EMAIL,
    "username": "Trần Minh Quân",
    "intro": "Backend Engineer · Python / FastAPI · đang tìm việc tại Tokyo",
    "resume": {**DEMO_RESUME, "email": DEMO_EMAIL},
}

# Bản sinh đôi: giống hệt về kỹ năng và kinh nghiệm, CHỈ khác tiếng Nhật.
# Chiếu hai danh sách cạnh nhau là bằng chứng rõ nhất rằng phần chấm điểm theo
# luật đang thật sự hoạt động — embedding thuần không làm được việc này, đo
# được hai CV kiểu này giống nhau tới 0.9871.
#
# BẮT BUỘC: mọi thứ đi vào `resume_text()` (chức danh, kỹ năng, mục tiêu, mô tả
# kinh nghiệm, dự án, học vấn) phải GIỐNG HỆT bản gốc. Chỉ được khác ở mục
# ngôn ngữ và chứng chỉ — hai thứ này không nằm trong văn bản đem đi embedding.
# Bản đầu tiên của file này có sửa một câu trong `objective` cho hợp văn cảnh,
# và chỉ riêng câu đó đã làm vector đổi theo, khiến chênh lệch điểm không còn
# quy được về trình độ tiếng Nhật nữa. Đo lại sau khi bỏ nhiễu: chênh tới 45
# điểm ở từng tin, top 20 chỉ còn trùng 11.
CONTRAST_ACCOUNT = {
    "email": CONTRAST_EMAIL,
    "username": "Trần Minh Quân (không biết tiếng Nhật)",
    "intro": "Cùng năng lực kỹ thuật, khác trình độ tiếng Nhật — dùng để so sánh",
    "resume": {
        **DEMO_RESUME,
        "email": CONTRAST_EMAIL,
        "name": "Trần Minh Quân (bản so sánh)",
        "languages": ["English - business level (TOEIC 850)", "Vietnamese - native"],
        "certificates": [c for c in DEMO_RESUME["certificates"] if not c[0].startswith("JLPT")],
        "japanese_level": None,
    },
}


def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _minimal_pdf(lines: list[str]) -> bytes:
    """Sinh một file PDF một trang hợp lệ, không cần thư viện ngoài.

    Chỉ dùng ASCII: font Helvetica dựng sẵn không có glyph tiếng Việt, viết
    tiếng Việt vào đây sẽ ra ký tự vỡ. Nội dung có ghi rõ đây là file demo để
    không ai nhầm là chứng chỉ thật.
    """
    body = ["BT", "/F1 18 Tf", "60 760 Td"]
    for index, line in enumerate(lines):
        body.append("0 -28 Td" if index else "0 0 Td")
        body.append(f"({_pdf_escape(line)}) Tj")
    body += ["0 -56 Td", "/F1 11 Tf", "(DEMO FILE - generated by scripts/seed_demo_user.py) Tj", "ET"]
    stream = "\n".join(body).encode("ascii", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


def _certificate_slug(name: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in name]
    return "".join(keep).strip("-").replace("--", "-")[:48]


def _write_certificates(entries: list[tuple[str, list[str]]]) -> list[dict]:
    """Ghi file PDF chứng chỉ và trả về đúng cấu trúc mà `Resume.certificates` dùng."""
    CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for display_name, lines in entries:
        filename = f"{CERTIFICATE_PREFIX}{_certificate_slug(display_name)}.pdf"
        (CERTIFICATE_DIR / filename).write_bytes(_minimal_pdf(lines))
        result.append({"name": display_name, "url": f"public/certificates/{filename}"})
    return result


async def _upsert_user(account: dict, role_id, password_hash: str) -> User:
    user = await User.find_one(User.email == account["email"])
    if user is None:
        user = User(
            email=account["email"],
            password=password_hash,
            username=account["username"],
            address=account["resume"]["address"],
            intro=account["intro"],
            role=role_id,
        )
        await user.insert()
        # Đúng như luồng đăng ký thật: thiếu hai bản ghi này thì trang cá nhân
        # và chức năng theo dõi của tài khoản demo sẽ lỗi.
        await Follower(user=user.id).insert()
        await Following(user=user.id).insert()
        return user

    # Đã tồn tại: đặt lại mật khẩu để mật khẩu in ra cuối script luôn đúng.
    user.password = password_hash
    user.username = account["username"]
    user.intro = account["intro"]
    user.address = account["resume"]["address"]
    if role_id and not user.role:
        user.role = role_id
    await user.save()
    if not await Follower.find_one(Follower.user == user.id):
        await Follower(user=user.id).insert()
    if not await Following.find_one(Following.user == user.id):
        await Following(user=user.id).insert()
    return user


def fill_resume(resume: Resume, data: dict, certificates: list[dict]) -> Resume:
    """Đổ nội dung CV vào document. Thuần tuý, không chạm DB và không ghi file.

    Tách riêng khỏi `_upsert_resume` để `tests/test_seed_demo_user.py` kiểm được
    các tính chất mà buổi demo phụ thuộc vào (hai hồ sơ cùng văn bản, số năm tự
    khai khớp với mục kinh nghiệm) mà không cần Mongo.
    """
    resume.name = data["name"]
    resume.position = data["position"]
    resume.birthday = data["birthday"]
    resume.email = data["email"]
    resume.address = data["address"]
    resume.phone = data["phone"]
    resume.github = data["github"]
    resume.objective = data["objective"]
    resume.educationName = data["educationName"]
    resume.educationMajor = data["educationMajor"]
    resume.educationCompletion = data["educationCompletion"]
    resume.educationGPA = data["educationGPA"]
    resume.experiences = [dict(e) for e in data["experiences"]]
    resume.projects = [dict(p) for p in data["projects"]]
    resume.skills = list(data["skills"])
    resume.languages = list(data["languages"])
    resume.certificates = certificates

    # Mục "Mục tiêu nghề nghiệp" người dùng tự khai. Gán TRƯỚC `apply_profile`
    # vì hàm đó chỉ điền vào chỗ trống — giống hệt thứ tự trong `post_resume`,
    # tức là điều người dùng tự khai luôn thắng phần máy suy ra.
    resume.japanese_level = data["japanese_level"]
    resume.english_level = data["english_level"]
    resume.years_of_experience = data["years_of_experience"]
    resume.desired_salary_min = data["desired_salary_min"]
    resume.desired_locations = list(data["desired_locations"])

    apply_profile(resume)
    return resume


async def _upsert_resume(user: User, data: dict) -> Resume:
    resume = await Resume.find_one(Resume.user == user.id)
    if resume is None:
        resume = Resume(user=user.id)
    fill_resume(resume, data, _write_certificates(data["certificates"]))
    await resume.save()
    return resume


async def seed(with_contrast: bool) -> dict:
    role = await Role.find_one(Role.value == 0)
    if role is None:
        logger.warning("Chưa có dữ liệu roles trong DB — tài khoản demo sẽ không có vai trò")
    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")

    accounts = [DEMO_ACCOUNT] + ([CONTRAST_ACCOUNT] if with_contrast else [])
    created: list[dict] = []
    resumes: list[Resume] = []

    for account in accounts:
        user = await _upsert_user(account, role.id if role else None, password_hash)
        resume = await _upsert_resume(user, account["resume"])
        resumes.append(resume)
        created.append(
            {
                "email": account["email"],
                "japanese_level": resume.japanese_level,
                "skills_normalized": len(resume.skills_normalized),
                "years": resume.years_of_experience,
            }
        )

    vectors = await embed_texts([resume_text(r) for r in resumes])
    if vectors is None:
        # Không phải lỗi chí mạng: phần chấm điểm theo luật vẫn chạy, chỉ mất
        # phần xếp hạng theo ngữ nghĩa. Nói rõ để người demo biết mà bật lại.
        logger.warning(
            "Embedder không dùng được — CV demo chưa có vector. "
            "Bật service embedder rồi chạy lại, hoặc chạy `python -m scripts.backfill_resumes`."
        )
    else:
        model = get_model_name()
        for resume, vector in zip(resumes, vectors, strict=True):
            resume.embedding = vector
            resume.embedding_model = model
            resume.embedding_source_hash = text_hash(resume_text(resume))
            await resume.save()

    return {
        "accounts": created,
        "embedded": bool(vectors),
        "links": await _demo_links(resumes[0]),
    }


async def _demo_links(resume: Resume) -> dict:
    """Tìm sẵn hai tin để mở lúc demo, ứng với hai chức năng.

    Tin xếp đầu bảng gần như luôn là tin ứng viên đã đủ điều kiện — mở đúng tin
    đó thì phần "còn thiếu gì" trống trơn và người xem không thấy được chức
    năng thứ hai. Nên ở đây tìm luôn một tin CÒN RÀO CẢN để có cái mà chỉ.
    """
    jobs = await Job.find({"is_active": True}, projection_model=JobMatchView).to_list()
    if not jobs:
        return {}

    await job_index.ensure_loaded()
    similarities = await job_index.similarities(resume.embedding)
    scored = sorted(
        ((job, evaluate(job, resume, similarities.get(job.id))) for job in jobs),
        key=lambda pair: pair[1].score,
        reverse=True,
    )

    def first(predicate):
        return next((pair for pair in scored if predicate(pair[1])), None)

    def blocking_kinds(match) -> set[str]:
        return {gap.kind for gap in match.gaps if gap.blocking}

    # Ưu tiên tin bị chặn vì TIẾNG NHẬT: đó mới là câu chuyện chính của dự án.
    # Không có thì lấy tin bị chặn vì bất cứ lý do gì, miễn là có cái để chỉ.
    blocked = first(lambda m: "japanese_level" in blocking_kinds(m)) or first(lambda m: bool(blocking_kinds(m)))

    return {"qualified": first(lambda m: not blocking_kinds(m)), "blocked": blocked}


async def clean() -> dict:
    emails = [DEMO_EMAIL, CONTRAST_EMAIL]
    users = await User.find({"email": {"$in": emails}}).to_list()
    ids = [u.id for u in users]

    removed_files = 0
    if CERTIFICATE_DIR.exists():
        for path in CERTIFICATE_DIR.glob(f"{CERTIFICATE_PREFIX}*.pdf"):
            path.unlink()
            removed_files += 1

    if not ids:
        return {"users": 0, "resumes": 0, "certificate_files": removed_files}

    resumes = await Resume.find({"user": {"$in": ids}}).delete()
    await Follower.find({"user": {"$in": ids}}).delete()
    await Following.find({"user": {"$in": ids}}).delete()
    await User.find({"_id": {"$in": ids}}).delete()
    return {
        "users": len(ids),
        "resumes": resumes.deleted_count if resumes else 0,
        "certificate_files": removed_files,
    }


def _print_summary(result: dict) -> None:
    print("\n== Tai khoan demo da san sang ==")
    for account in result["accounts"]:
        print(f"  email    : {account['email']}")
        print(f"  mat khau : {DEMO_PASSWORD}")
        print(
            f"  ho so    : tieng Nhat={account['japanese_level'] or 'khong'}, "
            f"{account['years']} nam KN, {account['skills_normalized']} ky nang chuan hoa"
        )
        print()
    if not result["embedded"]:
        print("  LUU Y: chua tinh duoc vector (embedder tat) -> chi cham diem theo luat.\n")

    print("  Dang nhap tai http://localhost:5173/login roi mo:")
    print("    /match     -> cong ty phu hop voi CV nay")
    print("    /resume    -> xem CV day du")

    links = result["links"]
    if not links:
        print("\n  Kho viec lam dang RONG -> trang /match se khong co gi.")
        print("  Nap du lieu truoc:  python -m scripts.seed_jobs_from_fixtures\n")
        return

    for key, label in (("qualified", "da du dieu kien"), ("blocked", "con rao can")):
        pair = links.get(key)
        if not pair:
            continue
        job, match = pair
        print(f"\n    /match/jobs/{job.id}")
        print(f"      {job.title[:64]}")
        print(f"      {match.score:.1f} diem - {label}")
        for gap in match.gaps[:3]:
            print(f"        {'[chan]' if gap.blocking else '[ghi chu]'} {gap.message[:66]}")
    print()


async def main() -> int:
    parser = argparse.ArgumentParser(description="Tao tai khoan demo kem CV day du")
    parser.add_argument(
        "--contrast",
        action="store_true",
        help="Tao them tai khoan sinh doi khong biet tieng Nhat de so sanh ket qua",
    )
    parser.add_argument("--clean", action="store_true", help="Xoa tai khoan demo va file chung chi da sinh")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    await connect_db()
    await connect_redis()
    try:
        result = await clean() if args.clean else await seed(args.contrast)
    finally:
        await close_embedder()
        await close_redis()
        await close_db()

    if args.clean:
        print(result)
    else:
        _print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
