from datetime import datetime

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.utils.time import utc_now


class Company(Document):
    """Hồ sơ doanh nghiệp gom từ nhiều trang tuyển dụng.

    Khoá duy nhất là `name_normalized`, KHÔNG phải (source, source_id): cùng một
    công ty xuất hiện ở nhiều nguồn thì phải là MỘT bản ghi, nếu không danh sách
    "công ty phù hợp với bạn" sẽ hiện trùng lặp và số vị trí đang tuyển bị chia
    nhỏ. `sources` ghi lại nó đã thấy ở những nguồn nào.

    Giới hạn đã biết: chỉ gộp được biến thể cùng hệ chữ (xem
    `normalize_company_name` trong app/services/etl/extract.py).
    """

    name: str
    name_normalized: str
    sources: list[str] = Field(default_factory=list)

    # Nguồn của phần MÔ TẢ (hiện chỉ nihongo-engineer có trang hồ sơ riêng).
    profile_source: str | None = None
    profile_source_id: str | None = None
    profile_url: str | None = None

    website: str | None = None
    logo_url: str | None = None
    location: str | None = None
    prefecture: str | None = None
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    job_count: int = 0

    # Text đã làm sạch dùng để tính vector — giữ lại để tra được vì sao ra kết
    # quả đó và để biết khi nào cần tính lại.
    search_text: str = ""
    embedding: list[float] | None = None
    embedding_model: str | None = None

    crawled_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "companies"
        indexes = [
            IndexModel([("name_normalized", ASCENDING)], name="name_normalized_unique", unique=True),
            IndexModel([("job_count", ASCENDING)], name="job_count_idx"),
        ]
