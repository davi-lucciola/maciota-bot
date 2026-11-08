import pytest

from maciota_bot.agent.prompt import render


def test_render_fills_slots_rejects_missing_keys_and_drops_blank_lines() -> None:
    assert 'Ada' in render('audience_reply', autor='Ada')

    with pytest.raises(KeyError, match='autor'):
        render('audience_reply')

    context = render(
        'server',
        channel_id='42',
        guild_name='',
        guild_description='',
        channel_name='',
        channel_topic='',
    )
    assert 'canal 42' in context
    assert 'Servidor:' not in context
