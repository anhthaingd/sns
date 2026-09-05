# ---------- Stage 1: builder ----------
# Cài dependency vào một virtualenv riêng để stage runtime chỉ copy đúng thứ cần,
# không mang theo pip cache hay công cụ build.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

# Tạo user và các thư mục đích TRƯỚC khi tải browser.
# Quan trọng: chown ở đây chạy trên thư mục còn rỗng nên layer gần như 0 byte.
# Nếu chown sau khi `playwright install` thì Docker phải sao chép lại toàn bộ
# ~1GB bundle Chromium vào một layer mới (đúng lỗi bản trước mắc phải).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /ms-playwright /app/public/uploads /app/public/certificates \
    && chown -R appuser:appuser /ms-playwright /app

# Thư viện hệ thống Chromium cần — bước này phải chạy bằng root vì dùng apt.
RUN playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER appuser

# Tải bundle Chromium bằng chính user sẽ chạy app -> file sinh ra đã đúng chủ sở hữu.
# Chỉ tải "headless shell" (~340MB) chứ không tải bản Chromium có giao diện (~640MB):
# crawl luôn chạy headless, và Playwright >= 1.49 dùng headless shell cho chế độ đó.
RUN playwright install chromium-headless-shell

COPY --chown=appuser:appuser . .

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:3000/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "3000"]
