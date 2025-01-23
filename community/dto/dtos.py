from fastapi import Form
from pydantic import BaseModel, Field
from typing import List, Optional

from users.dtos import UserSimpleProfile


# -- 요청 DTO -- #


class PostCreateRequest(BaseModel):
    """게시글 생성 요청 DTO (문자열 필드)"""

    title: str = Field(..., description="게시글 제목")
    body: str = Field(..., description="게시글 내용")
    # Optional[List[str]]를 받고 싶다면, FastAPI의 Form(...)도 List[str] 지원
    tag_ids: Optional[List[int]] = Field(None, description="태그 id 리스트")

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        body: str = Form(...),
        tag_ids: Optional[List[int]] = Form(None),
    ) -> "PostCreateRequest":
        """
        FastAPI에서 Form Data를 통해 title/body/tag_names를 받기 위한 헬퍼.
        """
        return cls(title=title, body=body, tag_ids=tag_ids)


# -- 응답 DTO -- #
class PostCreateResponse(BaseModel):
    post_id: int
    message: str


class TagInfo(BaseModel):
    id: int
    name: str


class PostInfoBase(BaseModel):
    id: int
    title: str
    body: str
    writer: UserSimpleProfile
    created_at: str
    views: int
    likes: int


class PostDetailItemDto(PostInfoBase):
    tags: List[TagInfo]
    images: List[str]


class PostListItemDto(PostInfoBase):
    tags: List[TagInfo]
    images: List[str]


class PostListResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    results: List[PostListItemDto]


class PostDetailResponse(BaseModel):
    id: int
    title: str
    body: str
    writer: UserSimpleProfile
    tags: List[TagInfo]
    images: List[str]
    views: int
    likes: int
    created_at: str
    is_active: bool


class CommentBaseDto(BaseModel):
    id: int
    created_at: str
    content: str
    writer: UserSimpleProfile
    likes: int
    is_active: bool


class CommentDto(CommentBaseDto):
    replies: Optional[List[CommentBaseDto]]


class PostCommentRequest(BaseModel):
    content: str
