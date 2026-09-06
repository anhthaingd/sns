from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel

# Cùng thang với `LANGUAGE_LEVELS` trong app/models/job.py để so sánh trực tiếp
# được giữa "CV có gì" và "tin yêu cầu gì".
from app.models.job import LANGUAGE_LEVELS  # noqa: F401  (tái xuất cho tầng so khớp)


class Resume(Document):
    user: PydanticObjectId | None = None
    name: str | None = None
    avatar: dict | None = None
    position: str | None = None
    birthday: str | None = None
    email: str | None = None
    address: str | None = None
    phone: str | None = None
    github: str | None = None
    objective: str | None = None
    educationName: str | None = None
    educationMajor: str | None = None
    educationCompletion: str | None = None
    educationGPA: str | None = None
    experiences: list[dict] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    certificates: list[dict] = Field(default_factory=list)

    # --- Bổ sung cho chức năng gợi ý công ty phù hợp -----------------------
    # Tất cả đều OPTIONAL: 6 CV đã có trong DB không có các trường này và không
    # được phép hỏng. `scripts/backfill_resumes.py` suy ra từ dữ liệu cũ.
    #
    # Vì sao cần: đây là thị trường việc làm Nhật, nơi trình độ tiếng Nhật là
    # tiêu chí lọc số một, nhưng CV cũ chỉ lưu `languages: ["JP", "EN"]` — không
    # có trình độ. Đo được: embedding coi CV "không biết tiếng Nhật" và CV "N1"
    # giống nhau tới 0.9871, nên nếu không có trường này thì hai người hoàn toàn
    # khác nhau sẽ nhận cùng một danh sách gợi ý.
    japanese_level: str | None = None
    english_level: str | None = None
    years_of_experience: int | None = None
    desired_salary_min: int | None = None
    desired_locations: list[str] = Field(default_factory=list)
    desired_job_types: list[str] = Field(default_factory=list)

    # Kỹ năng đã quy về tên chuẩn trong app/data/skills.json. Giữ riêng với
    # `skills` (do người dùng tự gõ) để không sửa dữ liệu họ nhập.
    skills_normalized: list[str] = Field(default_factory=list)

    embedding: list[float] | None = None
    embedding_model: str | None = None
    # Băm của phần văn bản đã dùng để tính vector — đổi thì mới phải tính lại.
    embedding_source_hash: str | None = None

    class Settings:
        name = "resumes"
        indexes = [
            # Mọi request /api/resume và /api/match/* đều tra CV theo user.
            # Không có index thì mỗi lần gọi là một lần quét toàn bộ collection
            # (đo được: quét 253 bản ghi để lấy đúng 1).
            #
            # CỐ Ý KHÔNG đặt `unique` dù mỗi tài khoản chỉ nên có một CV:
            # Beanie tạo index lúc khởi động, nên chỉ cần một DB nào đó lỡ có
            # hai CV trùng user là backend không khởi động nổi. Đánh đổi giữa
            # "dữ liệu trùng" (vô hại, `find_one` vẫn chạy) và "app không lên"
            # thì chọn vế đầu.
            IndexModel([("user", ASCENDING)], name="user_idx"),
        ]


class ResumeMatchView(BaseModel):
    """Đúng những trường mà tầng so khớp cần.

    Tồn tại để `app/services/matching.py` khai báo rõ nó phụ thuộc vào cái gì,
    và để test dựng được hồ sơ mẫu mà không phải khởi tạo Beanie/Mongo.
    `Resume` có đủ các trường này nên truyền thẳng document vào cũng chạy.
    """

    japanese_level: str | None = None
    english_level: str | None = None
    years_of_experience: int | None = None
    desired_salary_min: int | None = None
    desired_locations: list[str] = Field(default_factory=list)
    skills_normalized: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
