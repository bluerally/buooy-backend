from tortoise import fields
from common.models import BaseModel


class Notification(BaseModel):
    type = fields.CharField(max_length=100, null=True)
    classification = fields.CharField(max_length=100, default="", null=True)
    related_id = fields.BigIntField(null=True)
    message = fields.TextField(null=True)
    is_global = fields.BooleanField(default=False)
    target_user = fields.ForeignKeyField(
        "models.User",
        related_name="target_notifications",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "notifications"


class NotificationRead(BaseModel):
    notification = fields.ForeignKeyField(
        "models.Notification",
        related_name="reads",
        null=True,
        on_delete=fields.SET_NULL,
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="read_notifications",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "notifications_read"
