from maciota_bot.client import MaciotaClient
from maciota_bot.config import settings
from maciota_bot.db import create_db_engine
from maciota_bot.logs import setup_logging
from maciota_bot.state import AppState, configure


def main() -> None:
    setup_logging()

    engine = create_db_engine(settings.database_url)
    client = MaciotaClient()

    state = AppState(engine=engine, tree=client.tree, agent=None, client=client)
    configure(state)

    client.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == '__main__':
    main()
