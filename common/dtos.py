from pydantic import BaseModel, Field
from typing import TypeVar, Optional

T = TypeVar("T")


class BaseResponse[T](BaseModel):  # type: ignore
    message: str = ""
    data: Optional[T] = Field(default=None)  # type: ignore


# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate
#
#     @classmethod
#     def validate(cls, v) -> ObjectId:
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid ObjectId")
#         return ObjectId(v)
#
#     @classmethod
#     def __get_pydantic_json_schema__(cls, field_schema) -> None:
#         field_schema.update(type="string")
#
#
# class MongoBaseModel(BaseModel):
#
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#
#     class Config:
#
#         json_encoders = {ObjectId: str}
