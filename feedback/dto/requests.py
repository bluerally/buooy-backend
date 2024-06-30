from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    content: str
