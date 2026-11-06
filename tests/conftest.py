import os
from pathlib import Path

import pytest

# Importing maciota_bot.config builds Settings immediately.
os.environ['DISCORD_TOKEN'] = 'test-token'

_KINDS = frozenset({'unit', 'integration'})


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    tests_root = Path(__file__).parent
    for item in items:
        parts = item.path.resolve().relative_to(tests_root).parts
        if not parts or parts[0] not in _KINDS:
            continue
        item.add_marker(getattr(pytest.mark, parts[0]))
        if len(parts) >= 3:
            item.add_marker(getattr(pytest.mark, parts[1]))
