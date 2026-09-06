"""CV của người dùng.

Nằm riêng vì đây là đầu vào của chức năng gợi ý công ty: mỗi lần lưu CV đều
phải sinh lại hồ sơ so khớp và vector (`_refresh_match_profile`).
"""

import logging

from app.controllers.user_common import parse_json
from app.models.resume import Resume
from app.services.embedding import embed_texts, get_model_name
from app.services.resume_profile import apply_profile, resume_text, text_hash
from app.utils.file_utils import delete_file
from app.utils.ids import to_object_id
from app.utils.responses import ok
from app.utils.serialization import serialize_doc

logger = logging.getLogger("fuurin.resume")


def _clean_form_value(raw: str | None) -> str | None:
    """Form multipart gửi chuỗi rỗng và "null" cho ô không điền."""
    if raw is None:
        return None
    value = raw.strip()
    return None if value in ("", "null", "undefined") else value


async def _refresh_match_profile(resume: Resume) -> None:
    """Sinh hồ sơ so khớp và vector cho CV vừa lưu.

    Không có bước này thì CV mới lưu sẽ không có trình độ tiếng Nhật, không có
    kỹ năng chuẩn hoá và không có vector — tức là chức năng gợi ý công ty coi
    như không thấy hồ sơ đó.

    Lỗi ở đây KHÔNG được làm hỏng việc lưu CV: người dùng đã bấm lưu và dữ liệu
    của họ đã nằm trong DB, cùng lắm là chạy `scripts.backfill_resumes` bù sau.
    """
    try:
        apply_profile(resume)
        text = resume_text(resume)
        # Chỉ tính lại vector khi nội dung thật sự đổi — mỗi lần gọi tốn một
        # vòng mạng sang service embedder.
        if text and resume.embedding_source_hash != text_hash(text):
            vectors = await embed_texts([text])
            if vectors:
                resume.embedding = vectors[0]
                resume.embedding_model = get_model_name()
                resume.embedding_source_hash = text_hash(text)
        await resume.save()
    except Exception:
        logger.exception("Không cập nhật được hồ sơ so khớp cho CV %s", resume.id)


def _filter_different_elements(arr1, arr2):
    different = [
        obj1
        for obj1 in arr1
        if not any(obj2.get("name") == obj1.get("name") and obj2.get("value") == obj1.get("value") for obj2 in arr2)
    ]
    different += [
        obj2
        for obj2 in arr2
        if not any(obj1.get("name") == obj2.get("name") and obj1.get("value") == obj2.get("value") for obj1 in arr1)
    ]
    return different


async def get_resume(decoded_user: dict):
    resume = await Resume.find_one(Resume.user == to_object_id(decoded_user["_id"], "user_id"))
    return ok(resume=serialize_doc(resume) if resume else None)


async def post_resume(
    decoded_user: dict,
    name: str = None,
    position: str = None,
    old_avatar: str = None,
    birthday: str = None,
    email: str = None,
    address: str = None,
    phone: str = None,
    github: str = None,
    objective: str = None,
    education_name: str = None,
    education_major: str = None,
    education_completion: str = None,
    education_gpa: str = None,
    certificates_name: str = None,
    old_certificates: str = None,
    edit_certificates: str = None,
    experiences: str = None,
    skills: str = None,
    languages: str = None,
    projects: str = None,
    japanese_level: str = None,
    english_level: str = None,
    years_of_experience: str = None,
    desired_salary_min: str = None,
    desired_locations: str = None,
    files: dict = None,
):
    user_id = to_object_id(decoded_user["_id"], "user_id")
    parse_old_avatar = parse_json(old_avatar)
    parse_certificate_name = parse_json(certificates_name) or []
    parse_old_certificates = parse_json(old_certificates) or []
    parse_edit_certificates = parse_json(edit_certificates) or []

    resume_data = {
        "user": user_id,
        "name": name,
        "position": position,
        "birthday": birthday,
        "email": email,
        "address": address,
        "phone": phone,
        "github": github,
        "objective": objective,
        "educationName": education_name,
        "educationMajor": education_major,
        "educationCompletion": education_completion,
        "educationGPA": education_gpa,
        "experiences": parse_json(experiences) or [],
        "skills": parse_json(skills) or [],
        "languages": parse_json(languages) or [],
        "projects": parse_json(projects) or [],
    }

    # Người dùng tự khai thì tin theo; bỏ trống thì suy từ nội dung CV ở dưới.
    for field, raw in (
        ("japanese_level", japanese_level),
        ("english_level", english_level),
        ("years_of_experience", years_of_experience),
        ("desired_salary_min", desired_salary_min),
    ):
        value = _clean_form_value(raw)
        if value is None:
            continue
        resume_data[field] = int(value) if field in ("years_of_experience", "desired_salary_min") else value

    locations = parse_json(desired_locations)
    if isinstance(locations, list):
        resume_data["desired_locations"] = [str(x) for x in locations if x]

    existed_resume = await Resume.find_one(Resume.user == user_id)
    if not existed_resume:
        resume = Resume(**resume_data)
        await resume.insert()
        await _refresh_match_profile(resume)
        return ok(code="resume.saved")

    if parse_old_certificates:
        for removed in _filter_different_elements(parse_old_certificates, parse_edit_certificates):
            await delete_file(removed.get("url", ""))

    avatar_files = files.get("avatar", []) if files else []
    if avatar_files:
        if parse_old_avatar and parse_old_avatar.get("url"):
            await delete_file(parse_old_avatar["url"])
        resume_data["avatar"] = {"name": avatar_files[0]["filename"], "url": avatar_files[0]["path"]}

    cert_files = files.get("certificates", []) if files else []
    if cert_files and parse_certificate_name:
        new_certs = [
            {"name": parse_certificate_name[i] if i < len(parse_certificate_name) else "", "url": cf["path"]}
            for i, cf in enumerate(cert_files)
        ]
        resume_data["certificates"] = parse_edit_certificates + new_certs
    else:
        resume_data["certificates"] = parse_edit_certificates

    await Resume.find_one(Resume.user == user_id).update({"$set": resume_data})

    updated = await Resume.find_one(Resume.user == user_id)
    if updated is not None:
        await _refresh_match_profile(updated)
    return ok(code="resume.saved")
