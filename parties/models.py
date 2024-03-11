from tortoise import fields
from enum import IntEnum
from common.models import BaseModel


class Party(BaseModel):
    title = fields.CharField(null=True, blank=True, max_length=255)
    body = fields.TextField(null=True, blank=True)
    gather_at = fields.DatetimeField(null=True, blank=True, description="모임 날짜")
    due_at = fields.DatetimeField(null=True, blank=True, description="마감 날짜")
    place_id = fields.BigIntField(null=True, blank=True)
    place_name = fields.CharField(null=True, blank=True, max_length=255)
    address = fields.CharField(null=True, blank=True, max_length=255)
    longitude = fields.FloatField(null=True, blank=True)
    latitude = fields.FloatField(null=True, blank=True)
    organizer_user = fields.ForeignKeyField(
        "models.User", related_name="parties", null=True, on_delete=fields.SET_NULL
    )
    participant_limit = fields.IntField(null=True, blank=True, default=0)
    participant_cost = fields.IntField(null=True, blank=True, default=0)
    sport = fields.ForeignKeyField(
        "models.Sport", related_name="parties", null=True, on_delete=fields.SET_NULL
    )
    is_active = fields.BooleanField(null=True, default=True)
    notice = fields.CharField(max_length=255, null=True, blank=True)
    participants = fields.ManyToManyField(
        "models.User",
        related_name="participated_parties",
        through="models.PartyParticipant",
    )

    class Meta:
        table = "parties"

    def __str__(self) -> str:
        return f"{self.id} - {self.title}"


class ParticipationStatus(IntEnum):
    PENDING = 0
    APPROVED = 1
    REJECTED = 2
    CANCELLED = 3


class PartyParticipant(BaseModel):
    participant_user = fields.ForeignKeyField(
        "models.User", null=True, on_delete=fields.SET_NULL
    )
    party = fields.ForeignKeyField("models.Party", null=True, on_delete=fields.SET_NULL)
    status = fields.IntEnumField(
        ParticipationStatus, default=ParticipationStatus.PENDING
    )

    class Meta:
        table = "party_participants"

    def __str__(self) -> str:
        return f"{self.id} - {self.party} - {self.participant_user} - {self.status}"


class PartyComment(BaseModel):
    commenter = fields.ForeignKeyField(
        "models.User", null=True, on_delete=fields.SET_NULL
    )
    party = fields.ForeignKeyField(
        "models.Party", null=True, on_delete=fields.SET_NULL, related_name="comments"
    )
    content = fields.TextField(null=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "party_comments"


class PartyLike(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    party = fields.ForeignKeyField(
        "models.Party", null=True, on_delete=fields.SET_NULL, related_name="likes"
    )

    class Meta:
        table = "party_likes"
