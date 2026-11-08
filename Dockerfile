FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:531f855bda2c73cd6ef67d56b733b357cea384185b3022bd09f05e002cd144ca AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim AS runtime

RUN groupadd --system --gid 999 maciota \
    && useradd --system --gid 999 --uid 999 --create-home --home-dir /home/maciota maciota

WORKDIR /app

COPY --from=builder --chown=maciota:maciota /app/.venv /app/.venv

RUN chown maciota:maciota /app

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/app/.venv/bin/python", "-m", "maciota_bot.entrypoint"]
CMD ["maciota-bot"]
