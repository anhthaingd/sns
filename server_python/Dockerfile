FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# `--with-deps` tự cài đúng thư viện hệ thống Chromium cần, không cần liệt kê apt thủ công.
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Chạy bằng user thường thay vì root.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p public/uploads public/certificates \
    && chown -R appuser:appuser /app /ms-playwright
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:3000/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "3000"]
