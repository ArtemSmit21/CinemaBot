FROM python:3.13-slim

RUN pip install --no-cache-dir uv

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

CMD ["/app/.venv/bin/python", "/app/src/cinemabot.py"]
