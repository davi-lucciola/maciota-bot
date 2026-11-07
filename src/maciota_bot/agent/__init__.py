from maciota_bot.agent.checkpointer import open_checkpointer
from maciota_bot.agent.graph import build_graph
from maciota_bot.agent.llm import get_chat_model
from maciota_bot.config import settings


class Agent:
    def __init__(
        self,
        *,
        checkpointer: object,
        light_model: object,
        reply_model: object,
    ) -> None:
        self._graph = build_graph(
            checkpointer,
            light_model=light_model,
            reply_model=reply_model,
        )

    async def execute(
        self,
        *,
        channel_id: int,
        message_id: int,
        author_name: str,
        content: str,
        trigger_type: str,
    ) -> str:
        result = await self._graph.ainvoke(
            {
                'messages': [('user', f'{author_name}: {content}')],
                'channel_id': channel_id,
                'message_id': message_id,
                'author_name': author_name,
                'trigger_type': trigger_type,
                'context_hook': '',
                'persona_style': '',
                'final_response': '',
                'approved': False,
            },
            {'configurable': {'thread_id': f'channel_{channel_id}'}},
        )
        return result.get('final_response') or ''


def build_agent() -> Agent:
    return Agent(
        checkpointer=open_checkpointer(settings.checkpoint_path),
        light_model=get_chat_model(settings.llm_light_model, temperature=0),
        reply_model=get_chat_model(settings.llm_model, temperature=0.8),
    )
