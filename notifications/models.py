from tortoise import fields
from common.models import BaseModel


class Notification(BaseModel):
    user = fields.ForeignKeyField(
        "models.User", related_name="user_party_notifications"
    )
    type = fields.CharField(max_length=100, null=True)
    related_id = fields.BigIntField(null=True)
    message = fields.TextField(null=True)
    is_read = fields.BooleanField(default=False)

    class Meta:
        table = "notifications"
