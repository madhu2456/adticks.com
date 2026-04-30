FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2, pillow, and other native packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

COPY . .

# Make entrypoint script executable
RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]
