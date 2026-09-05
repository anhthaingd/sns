FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # Thu muc cache cua fastembed; tai san o buoc duoi roi chi doc luc chay.
    FASTEMBED_CACHE_PATH=/models \
    EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Tai model NGAY LUC BUILD. Neu de toi luc chay moi tai thi:
#   - lan khoi dong dau tien mat vai phut,
#   - va demo khong co mang la service khong len duoc.
RUN python -c "\
import os; from fastembed import TextEmbedding; \
m = TextEmbedding(os.environ['EMBEDDING_MODEL']); \
print('so chieu:', len(next(iter(m.embed(['test'])))))"

# Chan moi ket noi ra Hugging Face luc chay: model da nam san trong image.
ENV HF_HUB_OFFLINE=1

RUN useradd --create-home --uid 10002 embedder && chown -R embedder:embedder /models
USER embedder

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request,json,sys; \
r=json.load(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3)); \
sys.exit(0 if r['status']=='ok' else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
