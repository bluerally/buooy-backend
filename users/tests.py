import pytest
from fastapi.testclient import TestClient
from tortoise.contrib.test import finalizer, initializer
from users.models import Certificate, CertificateName_Pydantic, CertificateLevel


@pytest.fixture(scope="module")
async def initialize_tests():
    initializer(["users.models"])
    yield
    await finalizer()


@pytest.fixture(scope="module")
def client(initialize_tests):
    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
async def test_data_certificates():
    certificates = [
        {"name": "AIDA TEST"},
        {"name": "SSI TEST"},
        {"name": "PADI TEST"},
        {"name": "CMAS TEST"},
    ]
    created_certificates = []
    for certificate in certificates:
        created_certificate = await Certificate.create(**certificate)
        created_certificates.append(created_certificate)
    return created_certificates


@pytest.mark.asyncio
async def test_certificate_list(client, test_data_certificates) -> None:
    correct_data = await test_data_certificates
    response = client.get("/api/user/certificates")
    assert response.status_code == 200
    correct_data_dicts = [
        await CertificateName_Pydantic.from_tortoise_orm(cert) for cert in correct_data
    ]
    assert response.json().get("status_code") == 200
    assert response.json().get("data") == [cert.dict() for cert in correct_data_dicts]


@pytest.fixture(scope="module")
async def test_data_certificate_levels(client):
    # 테스트 데이터 생성
    certificate = await Certificate.create(name="Test Certificate")
    level1 = await CertificateLevel.create(certificate=certificate, level="Level 1")
    level2 = await CertificateLevel.create(certificate=certificate, level="Level 2")

    return {"certificate": certificate, "levels": [level1, level2]}


@pytest.mark.asyncio
async def test_get_certificate_levels(client, test_data_certificate_levels):
    certificate_levels = await test_data_certificate_levels
    certificate_id = certificate_levels["certificate"].id
    response = client.get(f"/api/user/certificates/{certificate_id}/levels")
    assert response.status_code == 200

    data = response.json()
    assert data["status_code"] == 200
    assert len(data["data"]) == 2
    assert data["data"][0]["level"] == "Level 1"
    assert data["data"][1]["level"] == "Level 2"
