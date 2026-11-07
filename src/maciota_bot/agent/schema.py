from enum import StrEnum
from typing import Literal

from langchain.messages import HumanMessage
from pydantic import BaseModel, Field


class TriggerAction(StrEnum):
    SILENCE = 'silence'
    CHANNEL = 'channel'
    REPLY = 'reply'


class TriggerDecision(BaseModel):
    """Decide se o Maciota entra na conversa.

    Os campos seguem a ordem em que o modelo preenche: primeiro o
    raciocínio, depois a ação.
    """

    reasoning: str = Field(
        description=(
            'Primeiro campo. Uma ou duas frases sobre o que está '
            'acontecendo e se existe gancho para comentar.'
        )
    )
    action: TriggerAction = Field(
        description=(
            'Depois do raciocínio. silence = não enviar. '
            'channel = mensagem geral no canal. '
            'reply = responder a mensagem de uma pessoa da lista.'
        )
    )
    message_index: int | None = Field(
        description=(
            'Se action for reply, o índice da mensagem da pessoa na '
            'janela numerada, começando em 0 na mais antiga. '
            'Nos outros casos, null.'
        )
    )
    hook: str = Field(
        description='Uma frase com o gancho. Vazio se action for silence.'
    )


class AgentInput(BaseModel):
    channel_id: int
    message_id: int
    author_name: str
    content: str
    trigger_type: Literal['mention', 'proactive']
    guild_name: str | None = None
    guild_description: str | None = None
    channel_name: str | None = None
    channel_topic: str | None = None

    def to_state(self) -> dict[str, object]:
        return {
            'messages': [
                HumanMessage(
                    content=f'{self.author_name}: {self.content}',
                    id=str(self.message_id),
                )
            ],
            'channel_id': self.channel_id,
            'message_id': self.message_id,
            'author_name': self.author_name,
            'trigger_type': self.trigger_type,
            'guild_name': self.guild_name,
            'guild_description': self.guild_description,
            'channel_name': self.channel_name,
            'channel_topic': self.channel_topic,
            'context_hook': '',
            'persona_style': '',
            'final_response': '',
            'reply_to_message_id': None,
            'approved': False,
        }


class AgentOutput(BaseModel):
    text: str
    reply_to_message_id: int | None = None
