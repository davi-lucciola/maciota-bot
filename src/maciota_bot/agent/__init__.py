import aiosqlite
from langchain.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from maciota_bot.agent.graph import BotGraph, build_graph
from maciota_bot.agent.llm import get_chat_model
from maciota_bot.agent.schema import AgentInput, AgentOutput
from maciota_bot.config import settings


class Agent:
    def __init__(
        self,
        *,
        light_model: BaseChatModel,
        reply_model: BaseChatModel,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._checkpointer = checkpointer
        self._graph: BotGraph = build_graph(
            checkpointer,
            light_model=light_model,
            reply_model=reply_model,
        )

    async def aclose(self) -> None:
        if isinstance(self._checkpointer, AsyncSqliteSaver):
            await self._checkpointer.conn.close()

    async def execute(self, turn: AgentInput) -> AgentOutput:
        result = await self._graph.ainvoke(
            turn.to_state(),
            {'configurable': {'thread_id': f'channel_{turn.channel_id}'}},
        )
        reply_to = result.get('reply_to_message_id')
        return AgentOutput(
            text=result.get('final_response') or '',
            reply_to_message_id=reply_to if isinstance(reply_to, int) else None,
        )


async def build_agent() -> Agent:
    connection = await aiosqlite.connect(settings.checkpoint_path)
    saver = AsyncSqliteSaver(connection)
    await saver.setup()
    return Agent(
        checkpointer=saver,
        light_model=get_chat_model(settings.llm_light_model, temperature=0),
        reply_model=get_chat_model(settings.llm_model, temperature=0.8),
    )
