FROM python:3.12-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY crawler/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install supabase for dual-write
RUN pip install --no-cache-dir supabase>=2.5.0

RUN playwright install chromium

COPY crawler/ /app/crawler/
COPY config/ /app/config/

CMD ["python", "-m", "crawler", "--once"]
