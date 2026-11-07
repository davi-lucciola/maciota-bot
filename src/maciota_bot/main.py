from maciota_bot.agent import build_agent
from maciota_bot.client import build_discord_client
from maciota_bot.commands import build_command_tree
from maciota_bot.config import settings
from maciota_bot.db import create_db_engine
from maciota_bot.events import on_member_join, on_message, on_ready
from maciota_bot.logs import setup_logging
from maciota_bot.state import AppState, configure


def main() -> None:
    setup_logging()

    engine = create_db_engine(settings.database_url)
    client = build_discord_client()
    tree = build_command_tree(client)

    state = AppState(engine=engine, tree=tree, agent=build_agent(), client=client)
    configure(state=state)

    client.event(on_ready)
    client.event(on_message)
    client.event(on_member_join)

    client.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == '__main__':
    main()
