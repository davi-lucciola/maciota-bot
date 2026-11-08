from maciota_bot import logs
from maciota_bot.client import MaciotaClient
from maciota_bot.config import settings


def main() -> None:
    logs.setup_logging()
    client = MaciotaClient()
    client.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == '__main__':
    main()
