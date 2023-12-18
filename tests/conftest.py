import asyncio

from httpx import AsyncClient
import pytest

from common.test_config import drop_databases, db_init, clean_up


@pytest.fixture(scope="session")
def loop():
    _loop = asyncio.new_event_loop()
    yield _loop
    _loop.close()


@pytest.fixture(scope="function", autouse=True)
def prepare_db(request, loop):
    async def setup_db():
        await db_init(generate_schema=False)
        try:
            await drop_databases()
        except:  # noqa
            pass
        await db_init("sqlite://:memory:")

    loop.run_until_complete(setup_db())

    def finalizer():
        new_loop = asyncio.new_event_loop()
        new_loop.run_until_complete(clean_up())
        new_loop.close()

    request.addfinalizer(finalizer)


@pytest.fixture(scope="module")
def client():
    from main import app

    client = AsyncClient(base_url="http://test", app=app)
    yield client
