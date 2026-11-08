[Português](README.pt-BR.md)

# Maciota

Maciota is a Discord bot that sits in a guild channel and talks like another member: Brazilian Portuguese, short, and usually quiet. It also greets people who join the server.

## What it does

Maciota reads guild messages. It ignores other bots and direct messages.

It speaks Brazilian Portuguese and stays quiet by default. A mention makes it reply to that message. Otherwise it joins when someone addresses him by name or with an insult, or when a line is absurd enough that he has not already commented. When it answers a person, the message is a reply to that person's message.

A new member who is not a bot gets a short joke in Brazilian Portuguese. The message goes to the channel saved for that server. If none is saved, it goes to the server's system channel. If that channel is also missing, nothing is sent.

`/welcome` only runs in a server. An administrator sets the welcome channel with that command and a text channel in the same server. The confirmation is ephemeral. Anyone who is not an administrator, or a channel from another server, gets a refusal.

`/acidity` only runs in a server. An administrator sets how sharp Maciota is: `mild`, `medium`, or `sharp`. A server that has never set it uses `medium`. A higher level is more ironic and more willing to swear. The confirmation is ephemeral. Anyone who is not an administrator gets a refusal.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- A Discord bot token
- An [OpenRouter](https://openrouter.ai/) API key, used for channel replies

In the Discord developer portal, enable the privileged **Message Content** and **Server Members** intents. The bot asks for both when it connects.

## Configure

Copy the example environment and fill the two secrets. Do not commit `.env`.

```bash
cp .env.example .env
```

| Variable | Required | Default |
| --- | --- | --- |
| `DISCORD_TOKEN` | yes | |
| `OPENROUTER_API_KEY` | yes, for replies | |
| `DATABASE_URL` | no | `sqlite:///data/maciota.db` |
| `OPENROUTER_API_URL` | no | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | no | `openai/gpt-4o-mini` |
| `LLM_LIGHT_MODEL` | no | `openai/gpt-4o-mini` |
| `CHECKPOINT_PATH` | no | `data/checkpoints.db` |
| `LOG_LEVEL` | no | `INFO` |

`LOG_LEVEL` is one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

The process does not create `data/`. Create it before the first local run so SQLite can open the database and the conversation checkpoint.

```bash
mkdir -p data
```

## Run

```bash
uv sync
uv run maciota-bot
```

## Docker

From the repository root, with `.env` in place:

```bash
docker compose up --build
```

Compose reads `.env` and mounts `./data` at `/app/data`, which is where the database and the conversation checkpoint are written.

## Tests

```bash
uv run ruff check
uv run ruff format --check
uv run pytest tests/unit
uv run pytest tests/integration
```
