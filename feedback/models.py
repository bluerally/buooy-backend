from common.models import BaseModel
from tortoise import fields


class Feedback(BaseModel):
    content = fields.TextField()

    class Meta:
        table = "feedbacks"
