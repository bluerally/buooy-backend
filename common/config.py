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

LOGIN_REDIRECT_URL = getenv("LOGIN_REDIRECT_URL", default="http://localhost:3000")

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


async def db_init() -> None:
    await Tortoise.init(
        config=TORTOISE_ORM,
        timezone="Asia/Seoul",
        modules={"models": ["users.models", "aerich.models", "parties.models"]},
    )
