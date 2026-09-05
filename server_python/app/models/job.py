from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.utils.time import utc_now

# Trình độ ngôn ngữ được chuẩn hoá về một thang duy nhất để so sánh được giữa
# các nguồn: GaijinPot ghi "Business level", DaiJob ghi "ビジネスレベル",
# tin khác ghi "N2". Thứ tự trong danh sách CHÍNH LÀ thứ tự so sánh.
LANGUAGE_LEVELS = ["none", "basic", "conversational", "business", "fluent", "native"]

# JLPT quy về cùng thang trên: N5 thấp nhất, N1 gần bản ngữ.
JLPT_TO_LEVEL = {
    "N5": "basic",
    "N4": "basic",
    "N3": "conversational",
    "N2": "business",
    "N1": "fluent",
}


class Job(Document):
    source: str
    source_id: str
    url: str
    title: str

    # Giữ CẢ ref lẫn tên thô: nhiều tin không đủ dữ liệu để dựng hồ sơ công ty,
    # nếu chỉ lưu ref thì mất luôn tên công ty đang hiển thị cho người dùng.
    company: PydanticObjectId | None = None
    company_name: str = ""

    location: str | None = None
    prefecture: str | None = None

    # Quy về YÊN/NĂM cho mọi nguồn: có nơi ghi lương tháng, có nơi ghi 万円/năm.
    # Không quy đổi thì bộ lọc "lương tối thiểu" cho kết quả sai lệch 12 lần.
    salary_min: int | None = None
    salary_max: int | None = None

    employment_type: str | None = None
    remote: bool = False

    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    required_japanese: str | None = None
    required_english: str | None = None
    min_years: int | None = None

    search_text: str = ""
    embedding: list[float] | None = None
    embedding_model: str | None = None

    posted_at: datetime | None = None
    crawled_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True

    class Settings:
        name = "jobs"
        indexes = [
            IndexModel([("source", ASCENDING), ("source_id", ASCENDING)], name="source_unique", unique=True),
            IndexModel([("is_active", ASCENDING), ("crawled_at", DESCENDING)], name="active_crawled_idx"),
            IndexModel([("required_japanese", ASCENDING)], name="japanese_idx"),
            IndexModel([("salary_min", ASCENDING)], name="salary_idx"),
            IndexModel([("prefecture", ASCENDING)], name="prefecture_idx"),
            IndexModel([("company", ASCENDING)], name="company_idx"),
        ]


class JobMatchView(BaseModel):
    """Bản chiếu của Job dùng cho việc so khớp — CỐ Ý không có `embedding`.

    Mỗi vector là 384 số thực; nạp cả 420 tin kèm vector là hơn 1MB đi qua mạng
    cho MỖI request, trong khi phần so khớp không cần tới chúng (độ tương đồng
    đã được tính sẵn trong chỉ mục ở bộ nhớ).
    """

    model_config = ConfigDict(populate_by_name=True)

    id: PydanticObjectId = Field(alias="_id")
    source: str = ""
    url: str = ""
    title: str = ""
    company: PydanticObjectId | None = None
    company_name: str = ""
    location: str | None = None
    prefecture: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    employment_type: str | None = None
    remote: bool = False
    required_skills: list[str] = Field(default_factory=list)
    required_japanese: str | None = None
    required_english: str | None = None
    min_years: int | None = None


class JobVectorView(BaseModel):
    """Chỉ `_id` và vector — dùng khi dựng chỉ mục tương đồng.

    Nạp cả document thì mỗi tin kéo theo mô tả tới 4000 ký tự mà chỉ mục không
    dùng tới; với vài trăm tin là vài MB đọc thừa mỗi lần làm mới.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: PydanticObjectId = Field(alias="_id")
    embedding: list[float] | None = None
