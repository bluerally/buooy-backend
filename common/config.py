import logging.config
from datetime import datetime
from logging import Handler, LogRecord, StreamHandler
from os import getenv
from pathlib import Path
from typing import Union, Dict, Any
from zoneinfo import ZoneInfo

from mixpanel import Mixpanel, Consumer
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from tortoise import Tortoise
from airtake import Airtake

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = "HS256"
TIME_ZONE = "Asia/Seoul"

APP_ENV_LOCAL = "local"
APP_ENV_PROD = "prod"
APP_ENV_TEST = "test"
APP_ENV = getenv("APP_ENV", APP_ENV_LOCAL)
IS_PRODUCTION = APP_ENV == APP_ENV_PROD
IS_TEST = APP_ENV == APP_ENV_TEST

LOGIN_REDIRECT_URL = getenv("LOGIN_REDIRECT_URL", default="http://localhost:3000")

# S3
S3_BUCKET = "buooy"
AWS_REGION = "ap-northeast-2"
AWS_S3_URL = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com"
AWS_S3_ACCESS_KEY = getenv("S3_ACCESS_KEY", default="")
AWS_S3_SECRET_KEY = getenv("S3_SECRET_KEY", default="")

MODELS_PATH = [
    "users.models",
    "parties.models",
    "aerich.models",
    "notifications.models",
    "feedback.models",
]

SQLITE_DB_URL = f"sqlite://{BASE_DIR}/db.sqlite3"

# DATABASE(MYSQL)
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

# TORTOISE ORM
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

# MONGO DB
MONGO_URI = getenv("MONGO_URI", default="mongodb://username:password@localhost:27017/")
MONGO_DATABASE = getenv("MONGODB_DATABASE", "blue-rally")
MONGO_LOGGING_COLLECTION = "logs"

# Mixpanel
MIXPANEL_TOKEN = getenv("MIXPANEL_TOKEN", "")
mixpanel_ins = Mixpanel(MIXPANEL_TOKEN, consumer=Consumer(verify_cert=False))

# Airtake
AIRTAKE_TOKEN = getenv("AIRTAKE_TOKEN", "")
airtake_ins = Airtake(token=AIRTAKE_TOKEN)

# 로깅 설정
# LOGGING_CONFIG = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "standard": {
#             "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(httpMethod)s - %(url)s - %(headers)s - %(queryParams)s - %(body)s",
#         },
#     },
#     "handlers": {
#         "info_file_handler": {
#             "level": "INFO",
#             "class": "logging.handlers.RotatingFileHandler",
#             "formatter": "standard",
#             "filename": str(BASE_DIR / "logs/info.log"),
#             "maxBytes": 1048576,  # 1MB
#             "backupCount": 5,
#         },
#         "error_file_handler": {
#             "level": "ERROR",
#             "class": "logging.handlers.RotatingFileHandler",
#             "formatter": "standard",
#             "filename": str(BASE_DIR / "logs/error.log"),
#             "maxBytes": 1048576,  # 1MB
#             "backupCount": 5,
#         },
#     },
#     "loggers": {
#         "bluerally.api": {
#             "handlers": ["info_file_handler", "error_file_handler"],
#             "propagate": False,
#         },
#     },
# }


class MongoLogHandler(Handler):
    def __init__(
        self,
        uri: str = "",
        database_name: str = "",
        collection_name: str = "",
    ) -> None:
        super().__init__()

        self.client = MongoClient(uri, server_api=ServerApi("1"))
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        # TTL 인덱스 설정
        # self.collection.create_index(
        #     [("timestamp", DESCENDING)], expireAfterSeconds=60 * 60 * 24 * 7
        # )

    def emit(self, record: LogRecord) -> None:
        document = {
            "timestamp": datetime.now(ZoneInfo(TIME_ZONE)),
            "level": record.levelname,
            "message": record.msg,
            "module": record.module,
            "path": record.pathname,
        }
        self.collection.insert_one(document)


logger = logging.getLogger("blue-rally-log")
logger.setLevel(logging.INFO)

if IS_TEST:
    console_handler = StreamHandler()
    logger.addHandler(console_handler)
if not IS_TEST:
    mongo_handler = MongoLogHandler(
        uri=MONGO_URI,
        database_name=MONGO_DATABASE,
        collection_name=MONGO_LOGGING_COLLECTION,
    )
    logger.addHandler(mongo_handler)


async def db_init() -> None:
    await Tortoise.init(
        config=TORTOISE_ORM,
        timezone=TIME_ZONE,
        modules={"models": MODELS_PATH},
    )
