from lai_bot.client import build_discord_client
from lai_bot.config import settings
from lai_bot.events import on_message, on_ready
from lai_bot.logs import setup_logging


def main() -> None:
    setup_logging()
    client = build_discord_client()
    
    client.event(on_ready)
    client.event(on_message)
    
    client.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == "__main__":
    main()
