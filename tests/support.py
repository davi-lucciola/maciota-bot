from maciota_bot.state import get_state

_disposed: set[int] = set()


class IdleTree:
    def __init__(self) -> None:
        self.synced = False

    async def sync(self) -> list[object]:
        self.synced = True
        return []


async def release_engine() -> None:
    engine = get_state().engine
    identity = id(engine)
    if identity in _disposed:
        return
    _disposed.add(identity)
    await engine.dispose()
