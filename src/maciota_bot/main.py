from maciota_bot.client import build_discord_client
from maciota_bot.commands import build_command_tree
from maciota_bot.config import settings
from maciota_bot.db import configure_engine, create_db_engine, init_db
from maciota_bot.events import on_member_join, on_message
from maciota_bot.events import on_ready as log_bot_connected
from maciota_bot.logs import setup_logging


def main() -> None:
    setup_logging()
    engine = create_db_engine(settings.database_url)
    init_db(engine)
    configure_engine(engine)

    client = build_discord_client()
    tree = build_command_tree(client)

    async def on_ready() -> None:
        await log_bot_connected()
        await tree.sync()

    client.event(on_ready)
    client.event(on_message)
    client.event(on_member_join)

    client.run(settings.discord_token.get_secret_value(), log_handler=None)


if __name__ == '__main__':
    main()
