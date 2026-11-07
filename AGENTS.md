# maciota-bot

## Architecture

`main` composes the process. It configures logging, opens the async database engine, builds the Discord client and the command tree, stores those shared instances, registers the event handlers, and starts the gateway.

`state` holds the shared instances the rest of the process reads: the async SQLAlchemy engine and the command tree. `main` creates that engine once and writes this state before `client.run`. Services and events read it with `get_state()`. A test that needs the engine or the tree publishes an `AppState` and clears it afterwards.

`db` opens the async engine through aiosqlite. `on_ready` creates the tables on the Discord event loop.

`models` defines the tables.

`commands` registers slash-command entrypoints. A handler calls a service and returns.

`events` owns every Discord event: `on_ready`, `on_message`, and `on_member_join`. `on_ready` creates the tables, logs that the bot connected, and syncs the command tree from state.

`services/welcome` builds the welcome text, reads and writes a guild's welcome channel, and performs the `/boas-vindas` use case: the user is an administrator, the channel belongs to the guild, the reply, and the saved row.

An event that needs a saved channel asks `welcome` for the id, then uses the Discord guild to resolve and send.

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

`tests/conftest.py` marks each test `unit` or `integration` from its directory, and marks the domain from the next directory (`client`, `config`, `events`, `logs`, `services`, `startup`, `state`). Add the marker in `pyproject.toml` when you add a domain directory.

`tests/conftest.py` sets `DISCORD_TOKEN` before the suite imports `maciota_bot.config`. A test that needs another token sets the environment and constructs `Settings()` itself.
