from maciota_bot.state import AppState, configure, get_state


async def release_engine() -> None:
    engine = get_state().engine
    configure(AppState())
    if engine is not None:
        await engine.dispose()
