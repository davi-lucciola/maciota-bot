import logging

import pytest

from maciota_bot.events import on_ready


async def test_on_ready_logs_that_the_bot_connected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger='maciota_bot.events')

    await on_ready()

    assert caplog.messages == ['Bot conectado']
