import logging.config
from typing import Any


def setup_logging() -> None:
    logging.config.dictConfig(_config())


def _config() -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[{asctime}] [{levelname:<8}] {name}: {message}",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "style": "{",
            },
        },
        "handlers": {
            "discord_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "discord.log",
                "encoding": "utf-8",
                "maxBytes": 32 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "standard",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            },
        },
        "loggers": {
            "discord": {
                "handlers": ["discord_file"],
                "level": "INFO",
                "propagate": False,
            },
            "discord.http": {
                "level": "INFO",
            },
            "maciota_bot": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
