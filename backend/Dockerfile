FROM python:3.12-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install crawler deps (needed by backend services)
COPY crawler/requirements.txt /app/requirements-crawler.txt
RUN pip install --no-cache-dir -r /app/requirements-crawler.txt

# Copy and install backend deps
COPY backend/requirements.txt /app/requirements-backend.txt
RUN pip install --no-cache-dir -r /app/requirements-backend.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY crawler/ /app/crawler/
COPY backend/ /app/backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
