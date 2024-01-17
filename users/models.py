from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

from common.models import BaseModel
from typing import Any


class Sport(BaseModel):
    name = fields.CharField(max_length=255)

    def __str__(self) -> Any:
        return self.name

    class Meta:
        table = "sports"


class Certificate(BaseModel):
    name = fields.CharField(max_length=255)

    def __str__(self) -> Any:
        return self.name

    class PydanticMeta:
        exclude = ["created_at", "updated_at"]

    class Meta:
        table = "certificates"


class CertificateLevel(BaseModel):
    certificate = fields.ForeignKeyField(
        "models.Certificate",
        related_name="certificate_levels",
        null=True,
        on_delete=fields.SET_NULL,
    )

    level = fields.CharField(max_length=100)

    def certificate_name(self) -> Any:
        if self.certificate and self.certificate.name:
            return self.certificate.name
        return ""

    def __str__(self) -> str:
        return f"{self.certificate.name} - {self.level}"

    class PydanticMeta:
        exclude = ["created_at", "updated_at"]

    class Meta:
        table = "certificate_levels"


class User(BaseModel):
    sns_id = fields.CharField(null=True, blank=True, max_length=255, index=True)
    name = fields.CharField(null=True, blank=True, max_length=255)
    email = fields.CharField(null=True, blank=True, max_length=255)
    phone = fields.CharField(null=True, blank=True, max_length=100)
    certificate_levels = fields.ManyToManyField(
        model_name="models.CertificateLevel",
        related_name="users",
        through="models.UserCertificate",
    )
    profile_image = fields.CharField(null=True, blank=True, max_length=255)
    profile_image_add = fields.CharField(null=True, blank=True, max_length=255)
    region = fields.CharField(null=True, blank=True, max_length=100)
    introduction = fields.TextField(null=True, blank=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"


# TODO user token 관리 테이블 조정 필요
class UserToken(BaseModel):
    user = fields.ForeignKeyField(
        "models.User", related_name="tokens", null=True, on_delete=fields.SET_NULL
    )
    refresh_token = fields.CharField(max_length=255, index=True)
    token_type = fields.CharField(max_length=50)
    expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "user_tokens"
        indexes = [("user", "is_active"), ("refresh_token",)]

    def __str__(self) -> str:
        return f"UserToken for {self.user.id} ({self.token_type}), expires_at: {self.expires_at.strftime('%Y-%m-%dT%H:%M:%SZ')}"


class UserCertificate(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    certificate_level = fields.ForeignKeyField(
        "models.CertificateLevel", null=True, on_delete=fields.SET_NULL
    )

    class Meta:
        table = "user_certificate_levels"

    def __str__(self) -> str:
        return f"USER: {self.user} - CERTIFICATE_LEVEL: {self.certificate_level}"


class UserInterestedSport(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    sport = fields.ForeignKeyField("models.Sport", null=True, on_delete=fields.SET_NULL)

    class Meta:
        table = "user_interested_sports"

    def __str__(self) -> str:
        return f"USER: {self.user} - SPORT: {self.sport}"


class AdminUser(BaseModel):
    username = fields.CharField(max_length=100, unique=True)
    password = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "admin_users"

    def __str__(self) -> str:
        return f"USER: {self.username}"


# Pydantic Model Creator
CertificateName_Pydantic = pydantic_model_creator(Certificate, name="certificate_name")
CertificateLevel_Pydantic = pydantic_model_creator(
    CertificateLevel, name="certificate_levels"
)
SportName_Pydantic = pydantic_model_creator(Sport, name="sports_name")
