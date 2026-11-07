from pathlib import Path

from langchain.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from maciota_bot.agent import Agent
from maciota_bot.agent.checkpointer import open_checkpointer


class ScriptedModel:
    def __init__(self, replies: list[str]) -> None:
        self._replies = list(replies)
        self.seen: list[list[object]] = []

    async def ainvoke(self, messages: list[object]) -> AIMessage:
        self.seen.append(list(messages))
        if not self._replies:
            raise AssertionError('model called too many times')
        if len(self._replies) == 1:
            text = self._replies[0]
        else:
            text = self._replies.pop(0)
        return AIMessage(content=text)


def _agent(
    light: ScriptedModel,
    reply: ScriptedModel,
    checkpointer: object | None = None,
) -> Agent:
    return Agent(
        checkpointer=MemorySaver() if checkpointer is None else checkpointer,
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
) -> str:
    return await agent.execute(
        channel_id=channel_id,
        message_id=message_id,
        author_name='Ada',
        content=content,
        trigger_type=trigger_type,
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


async def test_mention_skips_the_hook_and_returns_the_reply() -> None:
    light = ScriptedModel(['ironia curta'])
    reply = ScriptedModel(['kkkkk intankavel'])
    agent = _agent(light, reply)

    text = await _say(agent, 'e ai')

    assert text == 'kkkkk intankavel'
    assert len(light.seen) == 1
    assert 'gancho claro' not in _system(light.seen[0])
    assert 'ironia curta' in _system(reply.seen[0])
    assert 'dois parágrafos' in _system(reply.seen[0])


async def test_proactive_refusal_sends_nothing() -> None:
    light = ScriptedModel(['NÃO'])
    reply = ScriptedModel(['não devia chegar'])
    agent = _agent(light, reply)

    text = await _say(agent, 'só um oi', trigger_type='proactive')

    assert not text
    assert len(light.seen) == 1
    assert 'gancho claro' in _system(light.seen[0])
    assert reply.seen == []


async def test_proactive_hook_reaches_the_reply() -> None:
    light = ScriptedModel(['SIM\no controle sumiu', 'zoeira direta'])
    reply = ScriptedModel(['sumiu mesmo'])
    agent = _agent(light, reply)

    text = await _say(agent, 'cadê o controle', trigger_type='proactive')

    assert text == 'sumiu mesmo'
    assert 'o controle sumiu' in _system(reply.seen[0])
    assert 'zoeira direta' in _system(reply.seen[0])


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
    checkpointer = open_checkpointer(str(tmp_path / 'checkpoints.sqlite'))
    light = ScriptedModel(['ironia curta'])
    reply = ScriptedModel(['ok'])
    agent = _agent(light, reply, checkpointer)

    await _say(agent, 'segredo', channel_id=1, message_id=1)
    await _say(agent, 'de novo', channel_id=1, message_id=2)
    assert 'Ada: segredo' in _conversation(reply.seen[-1])

    await _say(agent, 'outro', channel_id=2, message_id=3)
    conversation = _conversation(reply.seen[-1])
    assert 'Ada: segredo' not in conversation
    assert 'Ada: outro' in conversation
