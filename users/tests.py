import pytest
import asyncio
from fastapi.testclient import TestClient
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer
from users.models import User
from users.utils import create_refresh_token, create_access_token


@pytest.fixture(scope="module")
async def initialize_tests():
    initializer(["users.models"], db_url="sqlite://:memory:")
    # 테이블 스키마 생성
    await Tortoise.generate_schemas()
    yield
    await finalizer()


@pytest.fixture(scope="module")
def client(initialize_tests):
    from main import app

    with TestClient(app) as c:
        yield c


# @pytest.fixture(scope="module")
# async def test_data_certificates():
#     certificates = [
#         {"name": "AIDA TEST"},
#         {"name": "SSI TEST"},
#         {"name": "PADI TEST"},
#         {"name": "CMAS TEST"},
#     ]
#     created_certificates = []
#     for certificate in certificates:
#         created_certificate = await Certificate.create(**certificate)
#         created_certificates.append(created_certificate)
#     return created_certificates
#
#
# @pytest.mark.asyncio
# async def test_certificate_list(client, test_data_certificates) -> None:
#     correct_data = await test_data_certificates
#     response = client.get("/api/user/certificates")
#     assert response.status_code == 200
#     correct_data_dicts = [
#         await CertificateName_Pydantic.from_tortoise_orm(cert) for cert in correct_data
#     ]
#     assert response.json().get("status_code") == 200
#     assert response.json().get("data") == [cert.dict() for cert in correct_data_dicts]
#
#
# @pytest.fixture(scope="module")
# async def test_data_certificate_levels(client):
#     # 테스트 데이터 생성
#     certificate = await Certificate.create(name="Test Certificate")
#     level1 = await CertificateLevel.create(certificate=certificate, level="Level 1")
#     level2 = await CertificateLevel.create(certificate=certificate, level="Level 2")
#
#     return {"certificate": certificate, "levels": [level1, level2]}
#
#
# @pytest.mark.asyncio
# async def test_get_certificate_levels(client, test_data_certificate_levels):
#     certificate_levels = await test_data_certificate_levels
#     certificate_id = certificate_levels["certificate"].id
#     response = client.get(f"/api/user/certificates/{certificate_id}/levels")
#     assert response.status_code == 200
#
#     data = response.json()
#     assert data["status_code"] == 200
#     assert len(data["data"]) == 2
#     assert data["data"][0]["level"] == "Level 1"
#     assert data["data"][1]["level"] == "Level 2"


@pytest.fixture(scope="module")
def test_user_and_tokens():
    async def create_user_and_tokens():
        # 테스트 사용자 생성
        user = await User.create(name="Test User", email="test@example.com")

        # 테스트 사용자의 Access 토큰과 Refresh 토큰 생성
        access_token = create_access_token(data={"user_id": user.id})
        refresh_token = await create_refresh_token(user)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    return asyncio.run(create_user_and_tokens())


@pytest.mark.asyncio
async def test_logout(client, test_user_and_tokens) -> None:
    tokens = test_user_and_tokens
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = client.post("/api/user/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"


@pytest.mark.asyncio
async def test_refresh_token(client, test_user_and_tokens) -> None:
    tokens = test_user_and_tokens
    response = client.post(
        "/api/user/auth/token/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
