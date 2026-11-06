import logging
import logging.config
from typing import Any

_RESET = '\x1b[0m'
_TRACEBACK_COLOUR = '\x1b[31m'
_LEVEL_COLOURS = {
    logging.DEBUG: '\x1b[40;1m',
    logging.INFO: '\x1b[34;1m',
    logging.WARNING: '\x1b[33;1m',
    logging.ERROR: '\x1b[31m',
    logging.CRITICAL: '\x1b[41m',
}


class ColourFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        original_exc_text = record.exc_text
        colour = _LEVEL_COLOURS.get(record.levelno, '')
        record.levelname = f'{colour}{original_levelname:<8}{_RESET}'
        if record.exc_info:
            text = (
                original_exc_text
                if original_exc_text is not None
                else self.formatException(record.exc_info)
            )
            record.exc_text = f'{_TRACEBACK_COLOUR}{text}{_RESET}'

        style = self._style
        original_fmt = style._fmt
        style._fmt = original_fmt.replace('{levelname:<8}', '{levelname}', 1)
        try:
            return super().format(record)
        finally:
            style._fmt = original_fmt
            record.levelname = original_levelname
            record.exc_text = original_exc_text


def setup_logging() -> None:
    logging.config.dictConfig(_config())


def _config() -> dict[str, Any]:
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[{asctime}] [{levelname:<8}] {name}: {message}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'style': '{',
            },
            'colored': {
                'class': 'maciota_bot.logs.ColourFormatter',
                'format': '[{asctime}] [{levelname:<8}] {name}: {message}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'style': '{',
            },
        },
        'handlers': {
            'discord_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'discord.log',
                'encoding': 'utf-8',
                'maxBytes': 32 * 1024 * 1024,
                'backupCount': 5,
                'formatter': 'standard',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
            },
        },
        'loggers': {
            'discord': {
                'handlers': ['discord_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'discord.http': {
                'level': 'INFO',
            },
            'maciota_bot': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
