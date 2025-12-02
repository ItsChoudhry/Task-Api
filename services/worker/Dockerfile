FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY services/worker ./services/worker

# Install dependencies (including rq, redis)
RUN uv sync --frozen --no-cache

# No EXPOSE needed — RQ worker doesn't listen on HTTP

# This is the correct way to run RQ worker in 2025
CMD ["uv", "run", "rq", "worker", "tasks"]
