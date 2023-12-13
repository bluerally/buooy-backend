from os import getenv
from pathlib import Path

from tortoise import Tortoise

BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV_LOCAL = "local"
APP_ENV_PROD = "prod"
APP_ENV = getenv("APP_ENV", APP_ENV_LOCAL)
IS_PRODUCTION = APP_ENV == APP_ENV_PROD

SQLITE_DB_URL = f"sqlite://{BASE_DIR}/db.sqlite3"
if IS_PRODUCTION:
    DB_CONNECTION = {
        "engine": "tortoise.backends.asyncpg",
        "credentials": {
            "host": getenv("DB_HOST", "localhost"),
            "port": getenv("DB_PORT", "3306"),
            "user": getenv("DB_USER", "root"),
            "password": getenv("DB_PASSWORD", "123456"),
            "database": getenv("DB_NAME", "dive_match_db"),
        },
    }
elif APP_ENV == APP_ENV_LOCAL:
    DB_CONNECTION = SQLITE_DB_URL
else:
    # TEST 환경에서는 메모리 DB 사용
    DB_CONNECTION = "sqlite://:memory:"

DB_CONFIG = {
    "connections": {
        "default": DB_CONNECTION,
    },
    "apps": {
        "models": {
            "models": ["users.models", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init():
    await Tortoise.init(
        db_url=SQLITE_DB_URL, modules={"models": ["users.models", "aerich.models"]}
    )
