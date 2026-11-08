import logging
from pathlib import Path

import aiosqlite
import pytest
from langchain.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from maciota_bot.agent import Agent
from maciota_bot.agent.schema import (
    AgentInput,
    AgentOutput,
    TriggerAction,
    TriggerDecision,
)


class ScriptedModel:
    def __init__(self, replies: list[object]) -> None:
        self._replies = list(replies)
        self.seen: list[list[object]] = []

    def with_structured_output(self, schema: type[object]) -> '_Structured':
        return _Structured(self, schema)

    async def ainvoke(self, messages: list[object]) -> AIMessage:
        self.seen.append(list(messages))
        item = self._next()
        if not isinstance(item, str):
            raise AssertionError(item)
        return AIMessage(content=item)

    def _next(self) -> object:
        if not self._replies:
            raise AssertionError('model called too many times')
        if len(self._replies) == 1:
            return self._replies[0]
        return self._replies.pop(0)


class _Structured:
    def __init__(self, model: ScriptedModel, schema: type[object]) -> None:
        self._model = model
        self._schema = schema

    async def ainvoke(self, messages: list[object]) -> object:
        self._model.seen.append(list(messages))
        item = self._model._next()
        if not isinstance(item, self._schema):
            raise AssertionError(item)
        return item


def _agent(light: ScriptedModel, reply: ScriptedModel) -> Agent:
    return Agent(
        checkpointer=MemorySaver(),
        light_model=light,
        reply_model=reply,
    )


async def _say(
    agent: Agent,
    content: str,
    *,
    channel_id: int = 1,
    message_id: int = 1,
    trigger_type: str = 'mention',
    guild_name: str | None = None,
    channel_name: str | None = None,
) -> AgentOutput:
    return await agent.execute(
        AgentInput(
            channel_id=channel_id,
            message_id=message_id,
            author_name='Ada',
            content=content,
            trigger_type=trigger_type,
            guild_name=guild_name,
            channel_name=channel_name,
        )
    )


def _system(messages: list[object]) -> str:
    first = messages[0]
    return str(first.content)


def _conversation(messages: list[object]) -> list[str]:
    return [
        str(message.content)
        for message in messages
        if getattr(message, 'type', None) != 'system'
    ]


async def test_mention_skips_the_hook_and_returns_the_reply(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.agent.nodes')
    light = ScriptedModel(['ironia curta'])
    reply = ScriptedModel(['kkkkk intankavel'])
    agent = _agent(light, reply)

    text = await _say(agent, 'e ai', guild_name='Maciota', channel_name='geral')

    assert text.text == 'kkkkk intankavel'
    assert 'Decisão: mention, enviar resposta à mensagem 1' in caplog.text
    assert 'Estilo escolhido: ironia curta' in caplog.text
    assert 'Resposta gerada: kkkkk intankavel' in caplog.text
    assert text.reply_to_message_id == 1
    assert len(light.seen) == 1
    assert 'Decida se o Maciota entra' not in _system(light.seen[0])
    assert 'ironia curta' in _system(reply.seen[0])
    assert 'dois parágrafos' in _system(reply.seen[0])
    assert 'Servidor: Maciota.' in _system(reply.seen[0])
    assert 'Canal: geral.' in _system(reply.seen[0])
    assert 'Você está respondendo a mensagem de Ada.' in _system(reply.seen[0])


async def test_proactive_refusal_sends_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.agent.nodes')
    light = ScriptedModel([
        TriggerDecision(
            reasoning='não tem gancho',
            action=TriggerAction.SILENCE,
            message_index=None,
            hook='',
        )
    ])
    reply = ScriptedModel(['não devia chegar'])
    agent = _agent(light, reply)

    text = await _say(agent, 'só um oi', trigger_type='proactive')

    assert not text.text
    assert text.reply_to_message_id is None
    assert 'Decisão: silence, não enviar. não tem gancho' in caplog.text
    assert len(light.seen) == 1
    assert 'Decida se o Maciota entra' in _system(light.seen[0])
    assert reply.seen == []


async def test_proactive_channel_message_reaches_the_reply() -> None:
    light = ScriptedModel([
        TriggerDecision(
            reasoning='o controle sumiu',
            action=TriggerAction.CHANNEL,
            message_index=None,
            hook='o controle sumiu',
        ),
        'zoeira direta',
    ])
    reply = ScriptedModel(['sumiu mesmo'])
    agent = _agent(light, reply)

    text = await _say(agent, 'cadê o controle', trigger_type='proactive')

    assert text.text == 'sumiu mesmo'
    assert text.reply_to_message_id is None
    assert 'o controle sumiu' in _system(reply.seen[0])
    assert 'zoeira direta' in _system(reply.seen[0])
    assert 'Mensagem geral no canal' in _system(reply.seen[0])


async def test_proactive_reply_uses_the_message_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.agent.nodes')
    light = ScriptedModel([
        'ironia curta',
        TriggerDecision(
            reasoning='a Ada perdeu o controle',
            action=TriggerAction.REPLY,
            message_index=0,
            hook='o controle sumiu',
        ),
        'zoeira direta',
    ])
    reply = ScriptedModel(['sumiu mesmo', 'de novo'])
    agent = _agent(light, reply)

    await _say(agent, 'cadê o controle', message_id=10)
    text = await _say(
        agent,
        'alguém viu?',
        message_id=11,
        trigger_type='proactive',
    )

    assert text.text == 'de novo'
    assert text.reply_to_message_id == 10
    assert 'Você está respondendo a mensagem de Ada.' in _system(reply.seen[-1])
    assert (
        'Decisão: reply, enviar. gancho=o controle sumiu reply_to=10. '
        'a Ada perdeu o controle'
    ) in caplog.text


async def test_invalid_reply_index_falls_back_to_the_channel() -> None:
    light = ScriptedModel([
        TriggerDecision(
            reasoning='tem gancho, índice ruim',
            action=TriggerAction.REPLY,
            message_index=9,
            hook='o controle sumiu',
        ),
        'zoeira direta',
    ])
    reply = ScriptedModel(['sumiu mesmo'])
    agent = _agent(light, reply)

    text = await _say(agent, 'cadê o controle', trigger_type='proactive')

    assert text.text == 'sumiu mesmo'
    assert text.reply_to_message_id is None
    assert 'Mensagem geral no canal' in _system(reply.seen[0])


async def test_model_sees_only_the_last_thirty_messages() -> None:
    light = ScriptedModel(['ironia curta'])
    reply = ScriptedModel(['ok'])
    agent = _agent(light, reply)

    for index in range(16):
        await _say(agent, f'msg-{index}', message_id=index)

    conversation = _conversation(reply.seen[-1])
    assert len(conversation) == 30
    assert 'Ada: msg-0' not in conversation
    assert 'Ada: msg-15' in conversation
    assert len(_conversation(light.seen[-1])) == 30


async def test_sqlite_thread_is_per_channel(tmp_path: Path) -> None:
    light = ScriptedModel(['ironia curta'])
    reply = ScriptedModel(['ok'])
    connection = await aiosqlite.connect(tmp_path / 'checkpoints.db')
    saver = AsyncSqliteSaver(connection)
    await saver.setup()
    agent = Agent(light_model=light, reply_model=reply, checkpointer=saver)
    try:
        await _say(agent, 'segredo', channel_id=1, message_id=1)
        await _say(agent, 'de novo', channel_id=1, message_id=2)
        assert 'Ada: segredo' in _conversation(reply.seen[-1])

        await _say(agent, 'outro', channel_id=2, message_id=3)
        conversation = _conversation(reply.seen[-1])
        assert 'Ada: segredo' not in conversation
        assert 'Ada: outro' in conversation
    finally:
        await agent.aclose()
