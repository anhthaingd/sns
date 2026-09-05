"""Service tính vector ngữ nghĩa cho văn bản.

Tách riêng khỏi backend vì hai lý do:

1. Model + ONNX Runtime nặng khoảng 400MB. Nhét vào image `server` thì công sức
   thu nhỏ image (2.75GB -> 1.06GB) đổ sông đổ bể.
2. Đây là việc nặng CPU và không dùng DB. Tách ra thì sau này muốn nhân bản
   riêng phần này, hoặc đổi model, đều không đụng tới backend.

Service KHÔNG mở cổng ra ngoài host — chỉ backend trong mạng docker gọi được.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastembed import TextEmbedding
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("fuurin.embedder")

# Bắt buộc là model ĐA NGÔN NGỮ: dữ liệu trộn tiếng Nhật và tiếng Anh, CV có thể
# viết bằng tiếng Việt. Bản 384 chiều nặng 220MB, đủ tốt cho việc xếp hạng theo
# ngành nghề (đo được: CV giáo viên -> 5/5 job đầu bảng đúng ngành).
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

MAX_TEXTS_PER_REQUEST = 256
MAX_CHARS_PER_TEXT = 4000

_model: TextEmbedding | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _model
    logger.info("Đang nạp model %s", MODEL_NAME)
    _model = TextEmbedding(MODEL_NAME)
    # Chạy thử một lần để ONNX khởi tạo xong trước khi nhận request thật,
    # nếu không request đầu tiên phải chịu toàn bộ thời gian khởi động.
    dim = len(next(iter(_model.embed(["warmup"]))))
    logger.info("Model sẵn sàng, số chiều = %s", dim)
    yield
    _model = None


app = FastAPI(title="Fuurin Embedder", lifespan=lifespan)


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=MAX_TEXTS_PER_REQUEST)


class EmbedResponse(BaseModel):
    model: str
    dim: int
    vectors: list[list[float]]


@app.get("/health")
async def health():
    return {"status": "ok" if _model is not None else "loading", "model": MODEL_NAME}


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest) -> EmbedResponse:
    if _model is None:
        # 503 chứ không 500: backend biết đây là lỗi tạm thời và tự chuyển sang
        # chấm điểm thuần luật.
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Model chưa nạp xong")

    # Cắt bớt để một request bất thường không làm nghẽn cả service. Model chỉ
    # đọc vài trăm token đầu nên phần cắt đi gần như không ảnh hưởng kết quả.
    texts = [(t or " ")[:MAX_CHARS_PER_TEXT] for t in request.texts]
    vectors = [v.tolist() for v in _model.embed(texts)]
    return EmbedResponse(model=MODEL_NAME, dim=len(vectors[0]), vectors=vectors)
