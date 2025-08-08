FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen

COPY src/ ./src/
COPY main.py ./main.py

RUN useradd -m -u 1000 yomu && chown -R yomu:yomu /app

USER yomu

CMD ["sh", "-c", "uv run main.py --init-db --db-path /app/data/yomu.db && uv run main.py --config-file /app/data/config.yaml --db-path /app/data/yomu.db"]
