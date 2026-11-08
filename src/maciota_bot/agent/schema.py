from enum import StrEnum
from typing import Literal

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
            'acontecendo e por que entrar ou ficar quieto. O padrão é '
            'silence.'
        )
    )
    action: TriggerAction = Field(
        description=(
            'Depois do raciocínio. silence = não enviar, e é o padrão. '
            'channel = mensagem geral no canal, só quando a fala é pra '
            'sala inteira e não cabe marcar ninguém. '
            'reply = responder a mensagem de uma pessoa da lista.'
        )
    )
    message_index: int | None = Field(
        description=(
            'Se action for reply, o índice de uma mensagem de pessoa na '
            'janela numerada, começando em 0 na mais antiga. Nunca o '
            'índice de uma linha Maciota (você). Nos outros casos, null.'
        )
    )
    hook: str = Field(
        description=(
            'O que responder, numa frase, sem resumir o que acabou de '
            'acontecer. Vazio se action for silence.'
        )
    )


class BotInput(BaseModel):
    channel_id: int
    message_id: int
    author_name: str
    content: str
    trigger_type: Literal['mention', 'proactive']
    guild_name: str | None = None
    guild_description: str | None = None
    channel_name: str | None = None
    channel_topic: str | None = None


class AgentOutput(BaseModel):
    text: str
    reply_to_message_id: int | None = None
