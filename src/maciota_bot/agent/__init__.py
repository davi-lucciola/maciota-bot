import asyncio

import aiosqlite
from langchain.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from maciota_bot.agent.graph import BotGraph, build_graph
from maciota_bot.agent.llm import get_chat_model
from maciota_bot.agent.schema import AgentOutput, BotInput
from maciota_bot.agent.state import BotState
from maciota_bot.config import settings


class BotAgent:
    def __init__(
        self,
        *,
        light_model: BaseChatModel,
        reply_model: BaseChatModel,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._checkpointer = checkpointer
        self._channel_locks: dict[int, asyncio.Lock] = {}
        self._graph: BotGraph = build_graph(
            checkpointer,
            light_model=light_model,
            reply_model=reply_model,
        )

    async def aclose(self) -> None:
        if isinstance(self._checkpointer, AsyncSqliteSaver):
            await self._checkpointer.conn.close()

    async def execute(self, turn: BotInput) -> AgentOutput:
        channel_id = turn['channel_id']
        async with self._lock_for(channel_id):
            result: BotState = await self._graph.ainvoke(
                turn,
                {'configurable': {'thread_id': f'channel_{channel_id}'}},
            )

        return AgentOutput(
            text=result['final_response'],
            reply_to_message_id=result['reply_to_message_id'],
        )

    def _lock_for(self, channel_id: int) -> asyncio.Lock:
        lock = self._channel_locks.get(channel_id)

        if lock is None:
            lock = asyncio.Lock()
            self._channel_locks[channel_id] = lock

        return lock


async def build_agent() -> BotAgent:
    connection = await aiosqlite.connect(settings.checkpoint_path)
    saver = AsyncSqliteSaver(connection)
    await saver.setup()
    return BotAgent(
        checkpointer=saver,
        light_model=get_chat_model(settings.llm_light_model, temperature=0),
        reply_model=get_chat_model(settings.llm_model, temperature=0.8),
    )
