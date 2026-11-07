from maciota_bot.state import AppState, get_state

_disposed: set[int] = set()


class IdleTree:
    def __init__(self) -> None:
        self.synced = False

    async def sync(self) -> list[object]:
        self.synced = True
        return []


class IdleAgent:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def execute(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return ''


class IdleUser:
    def __init__(self) -> None:
        self.last_message: object | None = None

    def mentioned_in(self, message: object) -> bool:
        self.last_message = message
        return bool(getattr(message, 'mentioned', False))


class IdleClient:
    def __init__(self) -> None:
        self.user = IdleUser()


def make_state(
    engine: object,
    tree: object | None = None,
    agent: object | None = None,
    client: object | None = None,
) -> AppState:
    return AppState(
        engine=engine,
        tree=IdleTree() if tree is None else tree,
        agent=IdleAgent() if agent is None else agent,
        client=IdleClient() if client is None else client,
    )


async def release_engine() -> None:
    engine = get_state().engine
    identity = id(engine)
    if identity in _disposed:
        return
    _disposed.add(identity)
    await engine.dispose()
