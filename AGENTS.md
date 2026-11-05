# maciota-bot

## Verify

When you change Python under `src/` or `tests/`:

1. Lint with `uv run ruff check`. Done when it exits 0.
2. When the check reports a fixable issue, run `uv run ruff check --fix` and `uv run ruff format`. Done when `uv run ruff format --check` and `uv run ruff check` both exit 0.
3. Lint first, then the tests that match the change, then the full suite.
   - Unit: `uv run pytest tests/unit -x --cov=maciota_bot`
   - After the unit run: `uv run coverage html`
   - Integration: `uv run pytest tests/integration -x`
   - Full suite: unit, then integration.
   Done when both pytest commands exit 0.

## Tests

A test under `tests/unit/<domain>/` exercises one module through its public functions. Discord appears there only as a fake message or channel.

A test under `tests/integration/<domain>/` boots real composition: logging handlers, or `main` with the gateway replaced.

`tests/conftest.py` marks each test `unit` or `integration` from its directory, and marks the domain from the next directory (`client`, `config`, `events`, `logs`, `startup`). Add the marker in `pyproject.toml` when you add a domain directory.

`tests/conftest.py` sets `DISCORD_TOKEN` before the suite imports `maciota_bot.config`. A test that needs another token sets the environment and constructs `Settings()` itself.
