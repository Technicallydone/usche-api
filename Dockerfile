FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    wget \
    gnupg2 \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app
RUN chown appuser:appuser /app

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs
RUN mkdir -p /app/staticfiles && chown appuser:appuser /app/staticfiles
RUN mkdir -p /app/media && chown appuser:appuser /app/media

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "igs_backend.wsgi:application"]
