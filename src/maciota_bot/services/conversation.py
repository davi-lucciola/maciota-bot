import logging
from typing import Literal

import discord

from maciota_bot.agent.schema import AgentInput, AgentOutput
from maciota_bot.state import get_state

logger = logging.getLogger(__name__)


async def respond(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    guild = message.guild
    logger.debug(
        'Mensagem recebida no servidor %s de %s: %s',
        guild.name,
        message.author.display_name,
        message.content,
    )

    state = get_state()
    agent = state.agent
    if agent is None:
        logger.debug('Agente indisponível, mensagem não será enviada')
        return

    user = state.client.user
    trigger_type: Literal['mention', 'proactive'] = (
        'mention' if user is not None and user.mentioned_in(message) else 'proactive'
    )
    try:
        output = await agent.execute(_turn(message, trigger_type))
        await _send_output(message, output)
    except Exception:
        logger.exception('Falha ao responder no canal')


def _turn(
    message: discord.Message,
    trigger_type: Literal['mention', 'proactive'],
) -> AgentInput:
    channel = message.channel
    guild = message.guild
    assert guild is not None
    return AgentInput(
        channel_id=channel.id,
        message_id=message.id,
        author_name=message.author.display_name,
        content=message.content,
        trigger_type=trigger_type,
        guild_name=guild.name,
        guild_description=guild.description,
        channel_name=getattr(channel, 'name', None),
        channel_topic=getattr(channel, 'topic', None),
    )


async def _send_output(message: discord.Message, output: AgentOutput) -> None:
    if not output.text.strip():
        logger.debug('Decisão: não enviar, resposta vazia')
        return

    reference = None
    guild = message.guild
    assert guild is not None
    if output.reply_to_message_id is not None:
        logger.debug(
            'Decisão: enviar resposta à mensagem %s',
            output.reply_to_message_id,
        )
        reference = discord.MessageReference(
            message_id=output.reply_to_message_id,
            channel_id=message.channel.id,
            guild_id=guild.id,
        )
    else:
        logger.debug('Decisão: enviar mensagem no canal')
    await message.channel.send(output.text, reference=reference)
