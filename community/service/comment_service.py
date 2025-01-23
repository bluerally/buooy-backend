from typing import Optional, List
from fastapi import HTTPException, status

from common.constants import FORMAT_YYYY_MM_DD_T_HH_MM_SS
from community.dto.dtos import CommentBaseDto, CommentDto
from community.models import (
    Post,
    PostComment,
    PostCommentLike,
    PostCommentReply,
    PostCommentReplyLike,
)
from users.dtos import UserSimpleProfile
from users.models import User


class CommentService:
    """
    댓글 / 댓글 좋아요
    """

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user

    async def create_comment(self, post_id: int, content: str) -> None:
        post = await Post.get_or_none(id=post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post({post_id}) not found",
            )
        await PostComment.create(post=post, writer=self.user, content=content)

    async def update_comment(self, comment_id: int, content: str) -> None:
        comment = await PostComment.get_or_none(id=comment_id)
        if not comment or not comment.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if self.user and comment.writer_id != self.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No permission to update"
            )

        comment.content = content
        await comment.save()

    async def delete_comment(self, comment_id: int) -> None:
        comment = await PostComment.get_or_none(id=comment_id)
        if not comment or not comment.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if self.user and comment.writer_id != self.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No permission to delete"
            )

        comment.is_active = False
        await comment.save()

    async def toggle_comment_like(self, comment_id: int) -> bool:
        """
        return: True -> 좋아요 생성됨, False -> 좋아요 취소됨
        """
        comment = await PostComment.get_or_none(id=comment_id)
        if not comment or not comment.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        existing_like = await PostCommentLike.get_or_none(
            user=self.user, comment=comment
        )
        if existing_like:
            await existing_like.delete()
            return False
        else:
            await PostCommentLike.create(user=self.user, comment=comment)
            return True

    async def _build_comment_writer_profile(
        self, user: Optional[User]
    ) -> UserSimpleProfile:
        """댓글 작성자 프로필 생성 헬퍼"""
        if user:
            return UserSimpleProfile(
                user_id=user.id,
                name=user.name,
                profile_picture=user.profile_image or "",
            )
        return UserSimpleProfile(user_id=0, name="Unknown", profile_picture="")

    async def _build_comment_base_dto(self, comment: PostComment) -> CommentBaseDto:
        """CommentBaseDto 생성 공통 로직"""
        likes_count = await PostCommentLike.filter(comment=comment).count()
        writer_profile = await self._build_comment_writer_profile(comment.user)

        return CommentBaseDto(
            id=comment.id,
            created_at=comment.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS),
            content=comment.content,
            writer=writer_profile,
            likes=likes_count,
            is_active=comment.is_active,
        )

    async def _build_reply_base_dto(self, reply: PostCommentReply) -> CommentBaseDto:
        """대댓글 CommentBaseDto 생성 공통 로직"""
        likes_count = await PostCommentReplyLike.filter(comment=reply).count()
        writer_profile = await self._build_comment_writer_profile(reply.user)

        return CommentBaseDto(
            id=reply.id,
            created_at=reply.created_at.strftime(FORMAT_YYYY_MM_DD_T_HH_MM_SS),
            content=reply.content,
            writer=writer_profile,
            likes=likes_count,
            is_active=reply.is_active,
        )

    async def get_post_comments_with_replies(self, post_id: int) -> List[CommentDto]:
        # 게시글 존재 여부 체크
        if not await Post.exists(id=post_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # 댓글 조회 (prefetch 포함)
        comments = (
            await PostComment.filter(post_id=post_id, is_active=True)
            .select_related("user")
            .prefetch_related("replies__user")
            .prefetch_related("replies")
            .prefetch_related("replies__likes")
            .order_by("-id")
        )

        result: List[CommentDto] = []
        for comment in comments:
            # 기본 댓글 정보 생성
            comment_base = await self._build_comment_base_dto(comment)

            active_replies = [r for r in comment.replies.all()]
            reply_list = [
                await self._build_reply_base_dto(reply) for reply in active_replies
            ]

            # 최종 댓글 DTO 생성
            result.append(CommentDto(**comment_base.model_dump(), replies=reply_list))

        return result


class ReplyService:
    """
    대댓글 / 대댓글 좋아요
    """

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user

    async def create_reply(self, comment_id: int, content: str) -> None:
        comment = await PostComment.get_or_none(id=comment_id)
        if not comment or not comment.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        await PostCommentReply.create(
            parent_comment=comment, writer=self.user, content=content
        )

    async def update_reply(self, reply_id: int, content: str) -> None:
        reply = await PostCommentReply.get_or_none(id=reply_id)
        if not reply or not reply.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found"
            )

        if self.user and reply.writer_id != self.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No permission to update"
            )

        reply.content = content
        await reply.save()

    async def delete_reply(self, reply_id: int) -> None:
        reply = await PostCommentReply.get_or_none(id=reply_id)
        if not reply or not reply.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found"
            )

        if self.user and reply.writer_id != self.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No permission to delete"
            )

        reply.is_active = False
        await reply.save()

    async def toggle_reply_like(self, reply_id: int) -> bool:
        """
        return: True -> 좋아요 생성됨, False -> 좋아요 취소됨
        """
        reply = await PostCommentReply.get_or_none(id=reply_id)
        if not reply or not reply.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found"
            )

        existing_like = await PostCommentReplyLike.get_or_none(
            user=self.user, comment=reply
        )
        if existing_like:
            await existing_like.delete()
            return False
        else:
            await PostCommentReplyLike.create(user=self.user, comment=reply)
            return True
