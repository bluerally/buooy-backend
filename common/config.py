import logging.config
from os import getenv
from pathlib import Path
from typing import Union, Dict, Any

from tortoise import Tortoise

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = "HS256"

APP_ENV_LOCAL = "local"
APP_ENV_PROD = "prod"
APP_ENV_TEST = "test"
APP_ENV = getenv("APP_ENV", APP_ENV_LOCAL)
IS_PRODUCTION = APP_ENV == APP_ENV_PROD
IS_TEST = APP_ENV == APP_ENV_TEST

LOGIN_REDIRECT_URL = getenv("LOGIN_REDIRECT_URL", default="http://localhost:3000")

# S3
S3_BUCKET = "blue-rally"
AWS_REGION = "ap-northeast-2"
AWS_S3_URL = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com"
AWS_S3_ACCESS_KEY = getenv("S3_ACCESS_KEY", default="")
AWS_S3_SECRET_KEY = getenv("S3_SECRET_KEY", default="")

# MODELS_PATH = ["users.models", "parties.models", "aerich.models", "notifications.models"]
MODELS_PATH = ["users.models", "parties.models", "aerich.models"]

SQLITE_DB_URL = f"sqlite://{BASE_DIR}/db.sqlite3"
# if IS_PRODUCTION:
DB_CONNECTION: Union[str, Dict[str, Any]]
if APP_ENV != APP_ENV_TEST:
    DB_CONNECTION = {
        "engine": "tortoise.backends.mysql",
        "credentials": {
            "host": getenv("DB_HOST", "localhost"),
            "port": getenv("DB_PORT", "3306"),
            "user": getenv("DB_USER", "root"),
            "password": getenv("DB_PASSWORD", "db_password"),
            "database": getenv("DB_NAME", "db_name"),
        },
    }
else:
    # TEST 환경에서는 메모리 DB 사용
    DB_CONNECTION = "sqlite://:memory:"

TORTOISE_ORM = {
    "connections": {
        "default": DB_CONNECTION,
    },
    "apps": {
        "models": {
            "models": MODELS_PATH,
            "default_connection": "default",
        }
    },
}

# 로깅 설정
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(httpMethod)s - %(url)s - %(headers)s - %(queryParams)s - %(body)s",
        },
    },
    "handlers": {
        "info_file_handler": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": str(BASE_DIR / "logs/info.log"),
            "maxBytes": 1048576,  # 1MB
            "backupCount": 5,
        },
        "error_file_handler": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": str(BASE_DIR / "logs/error.log"),
            "maxBytes": 1048576,  # 1MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "bluerally.api": {
            "handlers": ["info_file_handler", "error_file_handler"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("bluerally.api")


async def db_init() -> None:
    await Tortoise.init(
        config=TORTOISE_ORM,
        timezone="Asia/Seoul",
        modules={"models": MODELS_PATH},
    )
