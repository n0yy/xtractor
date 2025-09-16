# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY main.py ./

RUN uv pip install --system .

EXPOSE 8808

CMD ["uvicorn", "xtractor.api.app:app", "--host", "0.0.0.0", "--port", "8808"]
