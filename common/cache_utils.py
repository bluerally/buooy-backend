import json

import redis
import fakeredis
from contextlib import contextmanager
from typing import Iterator, Any
from os import getenv
from common.config import IS_TEST


class RedisManager:
    """Redis 클라이언트 관리자 클래스"""

    def __init__(self) -> None:
        self.redis_host = getenv("REDIS_HOST", "localhost")
        self.redis_port = int(getenv("REDIS_PORT", 6379))
        self.redis_db = int(getenv("REDIS_DB", 0))

    @contextmanager
    def _get_redis_client(self) -> Iterator[redis.Redis[Any]]:
        client = (
            fakeredis.FakeRedis()
            if IS_TEST
            else redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                # decode_responses=True
            )
        )

        try:
            yield client
        finally:
            # 필요에 따라 연결 해제 또는 추가 정리 작업을 수행
            client.close()

    def set_value(self, key: str, value: Any, expire: int = 60 * 60 * 7) -> None:
        with self._get_redis_client() as client:
            client.set(key, json.dumps(value), ex=expire)

    def get_value(self, key: str) -> Any:
        with self._get_redis_client() as client:
            value = client.get(key)
            return json.loads(value) if value else None

    def delete_value(self, key: str) -> None:
        with self._get_redis_client() as client:
            client.delete(key)
