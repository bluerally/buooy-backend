from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from starlette import status

from common.dependencies import get_current_user
from community.dto.dtos import (
    PostCreateResponse,
    PostCreateRequest,
    PostListResponse,
    PostDetailItemDto,
    CommentDto,
    PostCommentRequest,
)
from users.models import User
from community.service.post_service import PostService, PostViewService
from community.service.comment_service import CommentService, ReplyService

community_router = APIRouter(prefix="/api/community", tags=["Community"])


@community_router.post(
    "/post",
    response_model=PostCreateResponse,
    status_code=status.HTTP_201_CREATED,
    description="게시글 생성 (제목/본문/태그명 + 최대4장 이미지)",
)
async def create_post(
    form_data: PostCreateRequest = Depends(PostCreateRequest.as_form),
    image: List[UploadFile] = File(default=None),
    user: User = Depends(get_current_user),
) -> PostCreateResponse:
    """
    게시글 생성
    문자열 필드(title, body, tag_names)는 FormData로, 이미지 파일(images)은 File로 함께 받음.
    """
    service = PostService(user)
    new_post = await service.create_post(
        title=form_data.title,
        body=form_data.body,
        tag_ids=form_data.tag_ids,
        images=image,
    )
    return PostCreateResponse(post_id=new_post.id, message="Post created successfully")


@community_router.get(
    "/post", response_model=PostListResponse, status_code=status.HTTP_200_OK
)
async def get_posts(
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = Query(None),
) -> PostListResponse:
    """
    게시글 목록 (검색, 페이징)
    """
    service = PostViewService()
    data = await service.get_post_list(search=search, page=page, page_size=page_size)
    return data


@community_router.get(
    "/post/{post_id}", status_code=status.HTTP_200_OK, response_model=PostDetailItemDto
)
async def get_post_detail(post_id: int) -> PostDetailItemDto:
    """
    게시글 상세 + 조회수 증가
    """
    service = PostViewService()
    return await service.get_post_detail(post_id)


@community_router.post("/post/{post_id}/like", status_code=status.HTTP_200_OK)
async def toggle_post_like(
    post_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    게시글 좋아요 토글
    """
    service = PostService(user)
    result = await service.toggle_like(post_id)
    if result:
        return {"message": f"Post({post_id}) Liked"}
    else:
        return {"message": f"Post({post_id}) Unliked"}


# --------------------
# 댓글 / 대댓글
# --------------------
@community_router.get(
    "/post/{post_id}/comment",
    status_code=status.HTTP_200_OK,
    response_model=List[CommentDto],
)
async def get_comments_in_post(
    post_id: int, user: User = Depends(get_current_user)
) -> List[CommentDto]:
    """
    댓글 조회
    """
    service = CommentService(user)
    comments = await service.get_post_comments_with_replies(post_id)
    return comments


@community_router.post("/post/{post_id}/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int, body: PostCommentRequest, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    댓글 작성
    """
    service = CommentService(user)
    await service.create_comment(post_id, body.content)
    return {"message": "Comment created"}


@community_router.put("/comment/{comment_id}", status_code=status.HTTP_200_OK)
async def update_comment(
    comment_id: int, body: PostCommentRequest, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    댓글 수정
    """
    service = CommentService(user)
    await service.update_comment(comment_id, body.content)
    return {"message": "Comment updated"}


@community_router.delete("/comment/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    댓글 삭제(비활성화)
    """
    service = CommentService(user)
    await service.delete_comment(comment_id)
    return {"message": "Comment deleted"}


@community_router.post("/comment/{comment_id}/like", status_code=status.HTTP_200_OK)
async def toggle_comment_like(
    comment_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    댓글 좋아요 토글
    """
    service = CommentService(user)
    result = await service.toggle_comment_like(comment_id)
    return {"message": "Comment liked" if result else "Comment unliked"}


@community_router.post(
    "/comment/{comment_id}/reply", status_code=status.HTTP_201_CREATED
)
async def create_reply(
    comment_id: int, body: PostCommentRequest, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    대댓글 작성
    """
    service = ReplyService(user)
    await service.create_reply(comment_id, body.content)
    return {"message": "Reply created"}


@community_router.put("/comment/reply/{reply_id}", status_code=status.HTTP_200_OK)
async def update_reply(
    reply_id: int, body: PostCommentRequest, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    대댓글 수정
    """
    service = ReplyService(user)
    await service.update_reply(reply_id, body.content)
    return {"message": "Reply updated"}


@community_router.delete("/comment/reply/{reply_id}", status_code=status.HTTP_200_OK)
async def delete_reply(
    reply_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    대댓글 삭제(비활성화)
    """
    service = ReplyService(user)
    await service.delete_reply(reply_id)
    return {"message": "Reply deleted"}


@community_router.post("/comment/reply/{reply_id}/like", status_code=status.HTTP_200_OK)
async def toggle_reply_like(
    reply_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    대댓글 좋아요 토글
    """
    service = ReplyService(user)
    result = await service.toggle_reply_like(reply_id)
    return {"message": "Reply liked" if result else "Reply unliked"}
