from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

MESSAGE_WINDOW = 30


class BotState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    channel_id: int
    message_id: int
    author_name: str
    trigger_type: str
    guild_name: str | None
    guild_description: str | None
    channel_name: str | None
    channel_topic: str | None
    acidity: str
    context_hook: str
    persona_style: str
    final_response: str
    reply_to_message_id: int | None
    approved: bool
