import logging
from typing import Literal

import discord

from maciota_bot.agent.schema import Acidity, AgentOutput, BotInput
from maciota_bot.services.acidity import get_acidity
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
    acidity = await get_acidity(guild.id)
    referenced_author, referenced_excerpt = await _referenced(message)
    try:
        output = await agent.execute(
            _turn(
                message,
                trigger_type,
                acidity,
                referenced_author,
                referenced_excerpt,
            )
        )
        await _send_output(message, output)
    except Exception:
        logger.exception('Falha ao responder no canal')


async def _referenced(message: discord.Message) -> tuple[str | None, str | None]:
    reference = message.reference
    if reference is None or reference.message_id is None:
        return None, None
    quote = _quote(reference.resolved)
    if quote != (None, None):
        return quote
    try:
        resolved = await message.channel.fetch_message(reference.message_id)
    except discord.HTTPException:
        return None, None
    return _quote(resolved)


def _quote(resolved: object) -> tuple[str | None, str | None]:
    author = getattr(getattr(resolved, 'author', None), 'display_name', None)
    content = getattr(resolved, 'content', None)
    if not isinstance(author, str) and not isinstance(content, str):
        return None, None
    return (
        author if isinstance(author, str) else None,
        content if isinstance(content, str) else None,
    )


def _turn(
    message: discord.Message,
    trigger_type: Literal['mention', 'proactive'],
    acidity: Acidity,
    referenced_author: str | None,
    referenced_excerpt: str | None,
) -> BotInput:
    channel = message.channel
    guild = message.guild
    assert guild is not None
    return BotInput(
        channel_id=channel.id,
        message_id=message.id,
        author_name=message.author.display_name,
        content=message.content,
        created_at=message.created_at,
        trigger_type=trigger_type,
        guild_name=guild.name,
        guild_description=guild.description,
        channel_name=getattr(channel, 'name', None),
        channel_topic=getattr(channel, 'topic', None),
        acidity=acidity,
        referenced_author=referenced_author,
        referenced_excerpt=referenced_excerpt,
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
