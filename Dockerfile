FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72 AS runtime

RUN groupadd --system --gid 999 maciota \
    && useradd --system --gid 999 --uid 999 --create-home --home-dir /home/maciota maciota

WORKDIR /app

COPY --from=builder --chown=maciota:maciota /app/.venv /app/.venv

RUN mkdir -p /app/data \
    && chown maciota:maciota /app /app/data

ENV PATH="/app/.venv/bin:$PATH"

USER maciota

VOLUME ["/app/data"]

CMD ["maciota-bot"]
