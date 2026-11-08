[English](README.md)

# Maciota

O Maciota é um bot de Discord que fica num canal do servidor e fala como mais um membro: português do Brasil, curto, e quase sempre quieto. Ele também cumprimenta quem entra no servidor.

## O que ele faz

O Maciota lê mensagens do servidor. Ele ignora outros bots e mensagens diretas.

Ele fala português do Brasil e fica quieto por padrão. Uma menção faz ele responder àquela mensagem. Fora isso, ele entra quando alguém se dirige a ele pelo nome ou com um xingamento, ou quando surge uma fala absurda que ele ainda não comentou. Quando responde a uma pessoa, a mensagem é uma resposta à mensagem dessa pessoa.

Quem entra e não é bot recebe uma piada curta em português do Brasil. A mensagem vai para o canal salvo daquele servidor. Se nenhum foi salvo, vai para o canal de sistema. Se esse canal também não existir, nada é enviado.

`/welcome` só funciona num servidor. Um administrador define o canal de boas-vindas com esse comando e um canal de texto do mesmo servidor. A confirmação é efêmera. Quem não é administrador, ou um canal de outro servidor, recebe uma recusa.

`/acidity` só funciona num servidor. Um administrador define o quanto o Maciota é ácido: `mild`, `medium` ou `sharp`. Um servidor que nunca definiu usa `medium`. Quanto mais alto, mais irônico e mais disposto a xingar. A confirmação é efêmera. Quem não é administrador recebe uma recusa.

## Requisitos

- Python 3.13 ou mais novo
- [uv](https://docs.astral.sh/uv/)
- Um token de bot do Discord
- Uma chave de API da [OpenRouter](https://openrouter.ai/), usada nas respostas no canal

No portal de desenvolvedor do Discord, ative os intents privilegiados **Message Content** e **Server Members**. O bot pede os dois ao conectar.

## Configuração

Copie o ambiente de exemplo e preencha os dois segredos. Não faça commit do `.env`.

```bash
cp .env.example .env
```

| Variável | Obrigatória | Padrão |
| --- | --- | --- |
| `DISCORD_TOKEN` | sim | |
| `OPENROUTER_API_KEY` | sim, para as respostas | |
| `DATABASE_URL` | não | `sqlite:///data/maciota.db` |
| `OPENROUTER_API_URL` | não | `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | não | `openai/gpt-4o-mini` |
| `LLM_LIGHT_MODEL` | não | `openai/gpt-4o-mini` |
| `CHECKPOINT_PATH` | não | `data/checkpoints.db` |
| `LOG_LEVEL` | não | `INFO` |

`LOG_LEVEL` é um destes: `DEBUG`, `INFO`, `WARNING`, `ERROR` ou `CRITICAL`.

O processo não cria `data/`. Crie o diretório antes da primeira execução local para o SQLite abrir o banco e o checkpoint da conversa.

```bash
mkdir -p data
```

## Executar

```bash
uv sync
uv run maciota-bot
```

## Docker

Na raiz do repositório, com o `.env` no lugar:

```bash
docker compose up --build
```

O Compose lê o `.env` e monta `./data` em `/app/data`, onde ficam o banco e o checkpoint da conversa.

## Testes

```bash
uv run ruff check
uv run ruff format --check
uv run pytest tests/unit
uv run pytest tests/integration
```
