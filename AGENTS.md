# maciota-bot

## Architecture

`main` composes the process. It configures logging, opens the async database engine, builds `MaciotaClient`, stores the client, its command tree, and an empty agent, and starts the gateway. The `BotAgent` is not created here.

`client` is the Discord adapter. `MaciotaClient` subclasses `discord.Client` and builds the command tree. `on_ready` builds the agent when it is still empty, creates the tables, syncs the command tree, and logs that the bot connected. `close` closes the agent, then the Discord connection. `client/events` and `client/commands` are the inputs: each handler calls a service and returns.

`state` holds the shared instances the rest of the process reads: the async SQLAlchemy engine, the command tree, the Discord client, and the `BotAgent`. `main` writes this state before `client.run`, with the agent still empty. Services and entrypoints read it with `get_state()`. A test that needs one of them publishes an `AppState` and clears it afterwards.

`db` opens the async engine through aiosqlite. `on_ready` creates the tables on the Discord event loop.

`models` defines the tables.

`agent` answers a channel message. `BotAgent.execute` runs the LangGraph for that channel and returns the text to send and, when the bot is answering a person, that message id. The graph is compiled in the constructor with a required checkpointer. On ready that checkpointer is an AsyncSqliteSaver, in its own SQLite file. `get_session()` stays on the SQLModel tables.

`services/conversation` answers a guild message. It ignores a bot author, a direct message, and a missing agent, then calls `BotAgent.execute`. A reply target becomes a Discord message reference; otherwise the text goes to the channel.

`services/welcome` builds the welcome text, reads and writes a guild's welcome channel, greets a member who joins, and performs the `/welcome` use case: the user is an administrator, the channel belongs to the guild, the reply, and the saved row. `greet` resolves the saved channel on the guild and falls back to the system channel.

`services/acidity` reads and writes a guild's acidity (`mild`, `medium`, or `sharp`) and performs the `/acidity` use case. A guild with no row uses `medium`. `services/conversation` puts that level on the turn, and the reply prompt's acidity section and few-shot examples follow it.

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

`tests/conftest.py` marks each test `unit` or `integration` from its directory, and marks the domain from the next directory (`client`, `config`, `logs`, `services`, `startup`, `state`). Add the marker in `pyproject.toml` when you add a domain directory.

`tests/conftest.py` sets `DISCORD_TOKEN` before the suite imports `maciota_bot.config`. A test that needs another token sets the environment and constructs `Settings()` itself.
