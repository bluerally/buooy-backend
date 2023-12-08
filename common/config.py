from os import environ
from tortoise import Tortoise
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV_LOCAL = "local"
APP_ENV_PROD = "prod"
APP_ENV = environ.get("APP_ENV", APP_ENV_LOCAL)
IS_PRODUCTION = APP_ENV == APP_ENV_PROD

SQLITE_DB_URL = f"sqlite://{BASE_DIR}/db.sqlite3"
if IS_PRODUCTION:
    DB_CONNECTION = {
        "engine": "tortoise.backends.asyncpg",
        "credentials": {
            "host": environ.get("DB_HOST", "localhost"),
            "port": environ.get("DB_PORT", "3306"),
            "user": environ.get("DB_USER", "root"),
            "password": environ.get("DB_PASSWORD", "123456"),
            "database": environ.get("DB_NAME", "dive_match_db"),
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
