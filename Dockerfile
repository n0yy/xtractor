# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8808

WORKDIR /app

RUN groupadd --system app && useradd --system --no-create-home --gid app app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels xtractor \
    && rm -rf /wheels

RUN mkdir -p /app/.tmp && chown -R app:app /app

USER app

EXPOSE 8808

CMD ["sh", "-c", "uvicorn xtractor.api.app:app --host 0.0.0.0 --port ${PORT:-8808}"]
