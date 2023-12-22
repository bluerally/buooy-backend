from tortoise import fields

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
    participants = fields.ManyToManyField(
        "models.User",
        related_name="participated_parties",
        through="models.PartyParticipant",
    )

    class Meta:
        table = "parties"

    def __str__(self):
        return f"{self.id} - {self.title}"


class PartyParticipant(BaseModel):
    participant_user = fields.ForeignKeyField(
        "models.User", null=True, on_delete=fields.SET_NULL
    )
    party = fields.ForeignKeyField("models.Party", null=True, on_delete=fields.SET_NULL)
    is_active = fields.BooleanField(null=True, default=True)

    class Meta:
        table = "party_participants"

    def __str__(self):
        return f"{self.id} - {self.party} - {self.participant_user}"
