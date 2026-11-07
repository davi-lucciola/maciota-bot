import aiosqlite
from langchain.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.state import CompiledStateGraph

from maciota_bot.agent.graph import build_graph
from maciota_bot.agent.llm import get_chat_model
from maciota_bot.agent.schema import AgentInput, AgentOutput
from maciota_bot.config import settings


class Agent:
    def __init__(
        self,
        *,
        light_model: BaseChatModel,
        reply_model: BaseChatModel,
        checkpointer: BaseCheckpointSaver | None = None,
    ) -> None:
        self._light_model = light_model
        self._reply_model = reply_model
        self._connection: aiosqlite.Connection | None = None
        self._graph: CompiledStateGraph | None = None
        if checkpointer is not None:
            self._graph = build_graph(
                checkpointer,
                light_model=light_model,
                reply_model=reply_model,
            )

    async def setup(self, path: str) -> None:
        connection = await aiosqlite.connect(path)
        saver = AsyncSqliteSaver(connection)
        await saver.setup()
        self._connection = connection
        self._graph = build_graph(
            saver,
            light_model=self._light_model,
            reply_model=self._reply_model,
        )

    async def aclose(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            await connection.close()

    async def execute(self, turn: AgentInput) -> AgentOutput:
        if self._graph is None:
            raise RuntimeError('O agente ainda não abriu o checkpoint')

        result = await self._graph.ainvoke(
            turn.to_state(),
            {'configurable': {'thread_id': f'channel_{turn.channel_id}'}},
        )
        reply_to = result.get('reply_to_message_id')
        return AgentOutput(
            text=result.get('final_response') or '',
            reply_to_message_id=reply_to if isinstance(reply_to, int) else None,
        )


def build_agent() -> Agent:
    return Agent(
        light_model=get_chat_model(settings.llm_light_model, temperature=0),
        reply_model=get_chat_model(settings.llm_model, temperature=0.8),
    )
