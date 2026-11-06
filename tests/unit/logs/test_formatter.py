import logging
import sys
from types import TracebackType

from maciota_bot.logs import ColourFormatter

_INFO = '\x1b[34;1m'
_TRACEBACK = '\x1b[31m'
_RESET = '\x1b[0m'


def _record(
    *,
    level: int,
    msg: str,
    exc_info: (
        tuple[type[BaseException], BaseException, TracebackType]
        | tuple[None, None, None]
        | None
    ) = None,
) -> logging.LogRecord:
    return logging.LogRecord(
        name='maciota_bot',
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )


def test_format_colours_the_level_name_and_restores_the_record() -> None:
    formatter = ColourFormatter('[{levelname:<8}] {message}', style='{')
    record = _record(level=logging.INFO, msg='hello')

    rendered = formatter.format(record)

    assert rendered == f'[{_INFO}INFO    {_RESET}] hello'
    assert record.levelname == 'INFO'
    assert record.exc_text is None


def test_format_colours_the_traceback_and_restores_the_record() -> None:
    formatter = ColourFormatter('{message}', style='{')
    try:
        raise RuntimeError('boom')
    except RuntimeError:
        record = _record(level=logging.ERROR, msg='failed', exc_info=sys.exc_info())

    rendered = formatter.format(record)
    traceback = rendered.removeprefix('failed\n')

    assert traceback.startswith(f'{_TRACEBACK}Traceback (most recent call last):\n')
    assert 'RuntimeError: boom' in traceback
    assert traceback.endswith(_RESET)
    assert record.levelname == 'ERROR'
    assert record.exc_text is None
