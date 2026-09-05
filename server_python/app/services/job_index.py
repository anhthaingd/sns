"""Chỉ mục vector của tin tuyển dụng, giữ trong bộ nhớ tiến trình.

Vì sao không dùng vector database: ~700 tin × 384 chiều × 4 byte ≈ **1MB**.
Một phép nhân ma trận numpy trên chừng đó dữ liệu mất dưới 10ms — thêm hẳn một
hạ tầng mới chỉ để làm việc đó là đắt hơn nhiều so với lợi ích.

Chỉ mục được nạp lại khi ETL ghi dữ liệu mới. Dấu hiệu là khoá
`fuurin:jobs:version` trong Redis: ETL tăng số, mọi tiến trình backend thấy số
đổi thì tự nạp lại. Không có Redis thì rơi về hạn dùng theo thời gian.
"""

import logging
import time

import numpy as np
from beanie import PydanticObjectId

from app.config.redis_client import get_redis
from app.models.job import Job, JobVectorView

logger = logging.getLogger("fuurin.job_index")

JOBS_VERSION_KEY = "fuurin:jobs:version"

# Không có Redis thì đây là mức "cũ nhất chấp nhận được" của chỉ mục.
_FALLBACK_TTL_SECONDS = 300


async def bump_jobs_version() -> None:
    """ETL gọi sau khi ghi xong để mọi worker biết phải nạp lại chỉ mục."""
    redis = get_redis()
    if redis is None:
        return
    try:
        await redis.incr(JOBS_VERSION_KEY)
    except Exception:
        logger.warning("Không tăng được %s — chỉ mục sẽ tự làm mới theo thời gian", JOBS_VERSION_KEY)


async def _current_version() -> str | None:
    redis = get_redis()
    if redis is None:
        return None
    try:
        return await redis.get(JOBS_VERSION_KEY)
    except Exception:
        return None


class JobVectorIndex:
    def __init__(self) -> None:
        self.job_ids: list[PydanticObjectId] = []
        # Ma trận (n, dim) đã CHUẨN HOÁ độ dài về 1, nên cosine chỉ còn là một
        # phép nhân ma trận — không phải chia lại cho chuẩn ở mỗi lần truy vấn.
        self.matrix: np.ndarray | None = None
        self._version: str | None = None
        self._loaded_at: float = 0.0

    @property
    def size(self) -> int:
        return len(self.job_ids)

    async def _needs_reload(self) -> bool:
        if self.matrix is None:
            return True
        version = await _current_version()
        if version is not None:
            return version != self._version
        return (time.monotonic() - self._loaded_at) > _FALLBACK_TTL_SECONDS

    async def ensure_loaded(self) -> None:
        if not await self._needs_reload():
            return

        jobs = await Job.find(
            {"is_active": True, "embedding": {"$ne": None}},
            projection_model=JobVectorView,
        ).to_list()

        vectors = [j.embedding for j in jobs if j.embedding]
        self.job_ids = [j.id for j in jobs if j.embedding]

        if vectors:
            matrix = np.asarray(vectors, dtype=np.float32)
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            # Vector rỗng sẽ cho chuẩn 0 -> chia cho 0. Thay bằng 1 để dòng đó
            # thành vector 0, tức là không giống gì cả, thay vì thành NaN lan ra
            # toàn bộ kết quả.
            norms[norms == 0] = 1.0
            self.matrix = matrix / norms
        else:
            self.matrix = None

        self._version = await _current_version()
        self._loaded_at = time.monotonic()
        logger.info("Nạp chỉ mục: %s tin có vector", self.size)

    async def similarities(self, query: list[float] | None) -> dict[PydanticObjectId, float]:
        """Map job_id -> độ tương đồng cosine. Rỗng nếu chưa có vector nào."""
        await self.ensure_loaded()
        if self.matrix is None or not query:
            return {}

        vector = np.asarray(query, dtype=np.float32)
        if vector.shape[0] != self.matrix.shape[1]:
            # Đổi model giữa chừng: vector CV và vector tin khác số chiều.
            logger.warning(
                "Số chiều không khớp (CV %s, chỉ mục %s) — cần chạy lại ETL với --embed",
                vector.shape[0],
                self.matrix.shape[1],
            )
            return {}

        norm = float(np.linalg.norm(vector))
        if norm == 0:
            return {}
        scores = self.matrix @ (vector / norm)
        return dict(zip(self.job_ids, (float(s) for s in scores), strict=True))

    def clear(self) -> None:
        self.job_ids = []
        self.matrix = None
        self._version = None
        self._loaded_at = 0.0


job_index = JobVectorIndex()
