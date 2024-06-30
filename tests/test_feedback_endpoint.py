import pytest

from feedback.models import Feedback
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_success_feedback_post(client: AsyncClient) -> None:
    feedback_content = "이것좀 고쳐주세요!!"
    request_data = {
        "content": feedback_content,
    }
    # API 호출
    response = await client.post("/api/feedback", json=request_data)

    # 응답 검증
    assert response.status_code == 201
    assert await Feedback.get_or_none(content=feedback_content) is not None
