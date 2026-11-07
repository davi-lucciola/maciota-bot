from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

MESSAGE_WINDOW = 30


class BotState(TypedDict):
    messages: Annotated[list, add_messages]
    channel_id: int
    message_id: int
    author_name: str
    trigger_type: str
    context_hook: str
    persona_style: str
    final_response: str
    approved: bool
