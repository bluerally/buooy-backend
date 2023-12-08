from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.fields.base import SET_NULL

from common.models import BaseModel


class Certificate(BaseModel):
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name

    class PydanticMeta:
        exclude = ["created_at", "updated_at"]

    class Meta:
        table = "certificates"


class CertificateLevel(BaseModel):
    certificate = fields.ForeignKeyField(
        "models.Certificate", related_name="certificate_levels"
    )
    level = fields.CharField(max_length=100)

    def certificate_name(self) -> str:
        if self.certificate and self.certificate.name:
            return self.certificate.name
        return ""

    def __str__(self):
        return f"{self.certificate.name} - {self.level}"

    class PydanticMeta:
        exclude = ["created_at", "updated_at"]

    class Meta:
        table = "certificate_levels"


class User(BaseModel):
    name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
    password = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=100)
    certificate_levels = fields.ManyToManyField(
        model_name="models.CertificateLevel",
        related_name="users",
        through="models.UserCertificateLevel",
        on_delete=SET_NULL,
    )

    class Meta:
        table = "users"

    def __str__(self):
        return f"{self.id} - {self.name}"


class UserCertificate(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, blank=True)
    certificate_level = fields.ForeignKeyField(
        "models.CertificateLevel", null=True, blank=True
    )

    class Meta:
        table = "user_certificate_levels"

    def __str__(self):
        return f"USER: {self.user} - CERTIFICATE_LEVEL: {self.certificate_level}"


# Pydantic Model Creator
CertificateName_Pydantic = pydantic_model_creator(Certificate, name="certificate_name")
CertificateLevel_Pydantic = pydantic_model_creator(
    CertificateLevel, name="certificate_levels"
)
