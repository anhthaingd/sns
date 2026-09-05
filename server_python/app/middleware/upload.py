import os
import secrets
import time

from fastapi import Request, UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config.settings import UPLOAD_ROOT
from app.errors import ApiError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

MAX_IMAGES = 10
MAX_AVATARS = 1
MAX_CERTIFICATES = 10


def get_file_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower()


def generate_unique_filename(original_name: str) -> str:
    # Chỉ giữ tên file, bỏ mọi thành phần thư mục để chặn path traversal (../../etc/passwd).
    safe_name = os.path.basename(original_name or "file")
    unique_suffix = f"{int(time.time() * 1000)}-{secrets.randbelow(10**9)}"
    return f"{unique_suffix}-{safe_name}"


def _target_dir(ext: str, field_name: str) -> str:
    """Trả về thư mục lưu file dưới dạng đường dẫn tương đối (đúng với URL client dùng)."""
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "public/uploads"
    if ext in ALLOWED_PDF_EXTENSIONS:
        return "public/certificates"
    if field_name == "file":
        return "public/uploads/files"
    # ApiError chứ không phải ValueError: ValueError sẽ rơi vào chốt chặn 500
    # và người dùng chỉ thấy "Đã có lỗi xảy ra" — không biết là do sai định dạng.
    allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS))
    raise ApiError(400, f"Định dạng file không được hỗ trợ. Chỉ nhận: {allowed}")


async def save_upload_file(file: UploadFile, field_name: str = "images") -> dict:
    ext = get_file_extension(file.filename)
    rel_dir = _target_dir(ext, field_name)

    abs_dir = UPLOAD_ROOT.parent / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = generate_unique_filename(file.filename)

    # Kiểm tra kích thước TRƯỚC khi đọc: `await file.read()` nạp toàn bộ file
    # vào RAM, nên kiểm tra sau khi đọc thì file 2GB đã kịp làm sập tiến trình.
    # Starlette điền sẵn `size` từ Content-Length của phần multipart.
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise ApiError(413, f"File vượt quá {MAX_FILE_SIZE // (1024 * 1024)}MB.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ApiError(413, f"File vượt quá {MAX_FILE_SIZE // (1024 * 1024)}MB.")

    (abs_dir / filename).write_bytes(content)

    # `path` được lưu vào DB và client ghép thành `${BACKEND_URL}/${path}`,
    # nên bắt buộc là đường dẫn tương đối với dấu "/".
    return {"filename": filename, "path": f"{rel_dir}/{filename}"}


async def save_upload_files(
    images: list[UploadFile] | None = None,
    avatar: list[UploadFile] | None = None,
    certificates: list[UploadFile] | None = None,
) -> dict:
    result = {"images": [], "avatar": [], "certificates": []}

    for field, files, limit in (
        ("images", images, MAX_IMAGES),
        ("avatar", avatar, MAX_AVATARS),
        ("certificates", certificates, MAX_CERTIFICATES),
    ):
        for upload in (files or [])[:limit]:
            if not upload.filename:
                continue
            result[field].append(await save_upload_file(upload, field))

    return result


FILE_FIELD_LIMITS = {
    "images": MAX_IMAGES,
    "avatar": MAX_AVATARS,
    "certificates": MAX_CERTIFICATES,
}


async def save_uploaded_files(request: Request) -> dict:
    """FastAPI dependency: lưu mọi file upload trong multipart form.

    Client hiện tại luôn `formData.append('images', form.images)` kể cả khi
    không chọn ảnh, nên field tới server dưới dạng chuỗi "null". Backend Express
    cũ (multer) bỏ qua giá trị không phải file; FastAPI khai báo
    `List[UploadFile]` thì trả 422 và làm hỏng chức năng đăng bài / sửa hồ sơ.
    Dependency này giữ nguyên hành vi cũ: chỉ nhận phần tử thực sự là file.
    """
    empty = {field: [] for field in FILE_FIELD_LIMITS}
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        return empty

    form = await request.form()
    result = dict(empty)
    for field, limit in FILE_FIELD_LIMITS.items():
        uploads = [
            value
            for value in form.getlist(field)
            # request.form() trả về UploadFile của Starlette; fastapi.UploadFile là
            # lớp con nên isinstance với fastapi.UploadFile sẽ luôn False.
            if isinstance(value, StarletteUploadFile) and value.filename
        ]
        for upload in uploads[:limit]:
            result[field].append(await save_upload_file(upload, field))
    return result
