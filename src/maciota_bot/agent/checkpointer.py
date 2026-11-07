import sqlite3
from collections.abc import AsyncIterator, Sequence
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver


class SqliteCheckpointer(SqliteSaver):
    async def aget_tuple(self, config: dict) -> Any:
        return self.get_tuple(config)

    async def aput(
        self,
        config: dict,
        checkpoint: dict,
        metadata: dict,
        new_versions: dict,
    ) -> dict:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: dict,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = '',
    ) -> None:
        self.put_writes(config, writes, task_id, task_path)

    async def alist(
        self,
        config: dict | None,
        *,
        filter: dict | None = None,
        before: dict | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[Any]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item


def open_checkpointer(path: str) -> SqliteCheckpointer:
    connection = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteCheckpointer(connection)
    saver.setup()
    return saver
