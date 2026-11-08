import asyncio
import logging
from pathlib import Path

import aiosqlite
import pytest
from langchain.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from maciota_bot.agent import BotAgent
from maciota_bot.agent.schema import (
    Acidity,
    AgentOutput,
    BotInput,
    PersonaStyle,
    StyleDecision,
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


class _Loose:
    def __init__(self, model: ScriptedModel) -> None:
        self._model = model

    async def ainvoke(self, messages: list[object]) -> object:
        self._model.seen.append(list(messages))
        return self._model._next()


class _LooseModel(ScriptedModel):
    def with_structured_output(self, schema: type[object]) -> _Loose:
        return _Loose(self)


def _style(style: str) -> StyleDecision:
    return StyleDecision(reasoning='tom', style=style)


def _agent(light: ScriptedModel, reply: ScriptedModel) -> BotAgent:
    return BotAgent(
        checkpointer=MemorySaver(),
        light_model=light,
        reply_model=reply,
    )


async def _say(
    agent: BotAgent,
    content: str,
    *,
    channel_id: int = 1,
    message_id: int = 1,
    trigger_type: str = 'mention',
    guild_name: str | None = None,
    channel_name: str | None = None,
    acidity: Acidity = 'medium',
) -> AgentOutput:
    return await agent.execute(
        BotInput(
            channel_id=channel_id,
            message_id=message_id,
            author_name='Ada',
            content=content,
            trigger_type=trigger_type,
            guild_name=guild_name,
            channel_name=channel_name,
            acidity=acidity,
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
    light = ScriptedModel([_style('ironia curta')])
    reply = ScriptedModel(['kkkkk intankavel'])
    agent = _agent(light, reply)

    text = await _say(agent, 'e ai', guild_name='Maciota', channel_name='geral')

    system = _system(reply.seen[0])
    assert text.text == 'kkkkk intankavel'
    assert 'Decisão: mention, enviar resposta à mensagem 1' in caplog.text
    assert 'Estilo escolhido: ironia curta' in caplog.text
    assert 'Resposta gerada: kkkkk intankavel' in caplog.text
    assert text.reply_to_message_id == 1
    assert len(light.seen) == 1
    assert 'Decida se o Maciota entra' not in _system(light.seen[0])
    assert 'Estilo desta resposta: ironia curta.' in system
    assert 'rir' in system
    assert 'piada' in system
    assert 'zoar' in system
    assert 'informação pela metade' in system
    assert '**negrito**' in system
    assert 'dois parágrafos' in system
    assert 'você que some no meio da partida.' in system
    assert system.count('Maciota:') == 5
    assert 'Bia:' in system
    assert 'Servidor: Maciota.' in system
    assert 'Canal: geral.' in system
    assert 'Você está respondendo a mensagem de Ada.' in system
    headings = (
        'Quem você é',
        'Como fala',
        'Tamanho',
        'Limites',
        'Formatação',
        'Acidez',
        'Exemplos',
    )
    assert [system.index(heading) for heading in headings] == sorted(
        system.index(heading) for heading in headings
    )


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
    assert 'O padrão é ficar quieto' in _system(light.seen[0])
    assert reply.seen == []


async def test_proactive_channel_message_reaches_the_reply(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.agent.nodes')
    light = ScriptedModel([
        TriggerDecision(
            reasoning='o controle sumiu',
            action=TriggerAction.CHANNEL,
            message_index=None,
            hook='o controle sumiu',
        ),
        _style('zoeira direta'),
    ])
    reply = ScriptedModel(['sumiu mesmo'])
    agent = _agent(light, reply)

    text = await _say(agent, 'cadê o controle', trigger_type='proactive')

    assert text.text == 'sumiu mesmo'
    assert text.reply_to_message_id is None
    assert 'o controle sumiu' in _system(reply.seen[0])
    assert 'Estilo desta resposta: zoeira direta.' in _system(reply.seen[0])
    assert 'Mensagem geral no canal' in _system(reply.seen[0])
    assert 'Estilo escolhido: zoeira direta' in caplog.text


async def test_proactive_reply_uses_the_message_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.agent.nodes')
    light = ScriptedModel([
        _style('ironia curta'),
        TriggerDecision(
            reasoning='a Ada perdeu o controle',
            action=TriggerAction.REPLY,
            message_index=0,
            hook='o controle sumiu',
        ),
        _style('zoeira direta'),
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
    assert 'Maciota (você)' in _system(light.seen[1])
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
        _style('zoeira direta'),
    ])
    reply = ScriptedModel(['sumiu mesmo'])
    agent = _agent(light, reply)

    text = await _say(agent, 'cadê o controle', trigger_type='proactive')

    assert text.text == 'sumiu mesmo'
    assert text.reply_to_message_id is None
    assert 'Mensagem geral no canal' in _system(reply.seen[0])


async def test_model_sees_only_the_last_thirty_messages() -> None:
    light = ScriptedModel([_style('ironia curta')])
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
    light = ScriptedModel([_style('ironia curta')])
    reply = ScriptedModel(['ok'])
    connection = await aiosqlite.connect(tmp_path / 'checkpoints.db')
    saver = AsyncSqliteSaver(connection)
    await saver.setup()
    agent = BotAgent(light_model=light, reply_model=reply, checkpointer=saver)
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


class _HoldingModel(ScriptedModel):
    def __init__(
        self,
        replies: list[object],
        entered: asyncio.Event,
        release: asyncio.Event,
        second_entered: asyncio.Event,
    ) -> None:
        super().__init__(replies)
        self._entered = entered
        self._release = release
        self._second_entered = second_entered

    async def ainvoke(self, messages: list[object]) -> AIMessage:
        self.seen.append(list(messages))
        if len(self.seen) == 1:
            self._entered.set()
            await self._release.wait()
        else:
            self._second_entered.set()
        item = self._next()
        if not isinstance(item, str):
            raise AssertionError(item)
        return AIMessage(content=item)


async def test_same_channel_turns_do_not_overlap() -> None:
    entered = asyncio.Event()
    release = asyncio.Event()
    second_entered = asyncio.Event()
    light = ScriptedModel([_style('ironia curta')])
    reply = _HoldingModel(
        ['primeiro', 'segundo'],
        entered,
        release,
        second_entered,
    )
    agent = _agent(light, reply)

    first = asyncio.create_task(_say(agent, 'um', message_id=1))
    await entered.wait()
    second = asyncio.create_task(_say(agent, 'dois', message_id=2))
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(second_entered.wait(), timeout=0.05)

    release.set()
    assert (await first).text == 'primeiro'
    assert (await second).text == 'segundo'
    assert second_entered.is_set()
    assert _conversation(reply.seen[-1]) == [
        'Ada: um',
        'primeiro',
        'Ada: dois',
    ]


def test_style_decision_puts_reasoning_before_style() -> None:
    assert list(StyleDecision.model_fields) == ['reasoning', 'style']
    assert [item.value for item in PersonaStyle] == [
        'ironia curta',
        'zoeira direta',
        'explicativa',
        'bordão',
    ]


async def test_acidity_swaps_the_examples() -> None:
    light = ScriptedModel([_style('ironia curta')])
    reply = ScriptedModel(['ok'])
    agent = _agent(light, reply)

    await _say(agent, 'cadê o controle', message_id=1, acidity='mild')
    mild = _system(reply.seen[-1])
    await _say(
        agent,
        'cadê o controle',
        message_id=2,
        channel_id=2,
        acidity='sharp',
    )
    sharp = _system(reply.seen[-1])

    assert 'não xinga' in mild
    assert 'chama no canal de voz.' in mild
    assert mild.count('Maciota:') == 5
    assert 'Bia:' in mild
    assert 'cala a boca.' not in mild
    assert 'pode xingar' in sharp
    assert 'cala a boca.' in sharp
    assert sharp.count('Maciota:') == 5
    assert 'Bia:' in sharp


async def test_wrong_style_schema_fails() -> None:
    light = _LooseModel(['não é schema'])
    reply = ScriptedModel(['não devia'])
    agent = _agent(light, reply)

    with pytest.raises(TypeError, match='StyleDecision'):
        await _say(agent, 'e ai')

    assert reply.seen == []
