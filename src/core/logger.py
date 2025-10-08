import logging
import logging.config
from pathlib import Path
from datetime import datetime, timezone, timedelta
from core.dependencies import get_config

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        utc_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        local_dt = utc_dt.astimezone(timezone(timedelta(hours=5)))
        if datefmt:
            return local_dt.strftime(datefmt)
        return local_dt.isoformat()
    
    def format(self, record):
        if record.name.startswith("uvicorn"):
            record.custom_filename = "uvicorn"
        else:
            full_path = Path(record.pathname).resolve()
            try:
                relative_path = str(full_path).replace('/src/', '').replace('src/', '')
                record.custom_filename = relative_path
            except Exception:
                record.custom_filename = full_path.name

        try:
            record.levelname = f"{record.levelname:^7}"
        except Exception:
            pass

        s = super().format(record)

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            s = f"{s}\n{exc_text}"

        return s

FORMAT = "[%(asctime)s] [ %(levelname)s ] [%(custom_filename)s] %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": CustomFormatter,
            "format": FORMAT,
            "datefmt": DATEFMT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",  # Показываем info-логи uvicorn
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",  # Было WARNING — теперь INFO
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",  # Если хочешь видеть access-логи
            "handlers": ["console"],
            "propagate": False,
        },
        "celery": {
            "level": "DEBUG" if get_config().DEBUG else "INFO",
            "handlers": ["console"],
            "propagate": False,
         },
        "": {
            "level":  "DEBUG" if get_config().DEBUG else "INFO",
            "handlers": ["console"],
            "propagate": True,
        },
        "app_logger": {
            "level": "DEBUG" if get_config().DEBUG else "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
    "root": {
        "level": "ERROR",
        "handlers": ["console"],
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


logger = logging.getLogger("app_logger")