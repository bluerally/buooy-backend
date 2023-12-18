import pytest

from users.models import User


@pytest.mark.asyncio
async def test_person_model_creation():
    person = User(name="Myeongjin", email="Yang")
    await person.save()
    assert person == await User.first()
