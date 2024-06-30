from fastapi import APIRouter, status

from common.logging_configs import LoggingAPIRoute
from feedback.dto.requests import FeedbackRequest
from feedback.models import Feedback

feedback_router = APIRouter(
    prefix="/api/feedback",
    route_class=LoggingAPIRoute,
)


@feedback_router.post(
    "",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
async def post_feedback(request: FeedbackRequest) -> str:
    await Feedback.create(content=request.content)
    return "feedback created successfully"
