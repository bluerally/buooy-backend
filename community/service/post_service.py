from typing import List, Optional, Any
from fastapi import UploadFile, HTTPException, status
from tortoise.expressions import Q
from tortoise.transactions import atomic

from community.dto.dtos import (
    PostListResponse,
    PostListItemDto,
    TagInfo,
    PostDetailItemDto,
)
from community.models import Post, PostLike, PostImage, Tag, PostTag
from common.cache_utils import RedisManager
from common.cache_constants import (
    CACHE_KEY_POST_VIEWS,
    CACHE_KEY_POST_LIKES,
    VIEW_COUNT_UPDATE_THRESHOLD,
    CACHE_EXPIRE_TIME,
)
from users.dtos import UserSimpleProfile
from users.models import User
from common.utils import s3_upload_file


class PostService:
    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user
        self.redis = RedisManager()

    async def increment_view(self, post_id: int) -> None:
        cache_key = CACHE_KEY_POST_VIEWS.format(post_id=post_id)
        views_data = self.redis.get_value(cache_key)
        if views_data is None:
            post = await Post.get_or_none(id=post_id)
            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
                )
            views_data = {"count": post.views, "update_count": 0}

        views_data["count"] += 1
        views_data["update_count"] += 1
        self.redis.set_value(cache_key, views_data, expire=CACHE_EXPIRE_TIME)

        if views_data["update_count"] >= VIEW_COUNT_UPDATE_THRESHOLD:
            post = await Post.get_or_none(id=post_id)
            if post:
                post.views = views_data["count"]
                await post.save()
                views_data["update_count"] = 0
                self.redis.set_value(cache_key, views_data, expire=CACHE_EXPIRE_TIME)

    async def toggle_like(self, post_id: int) -> bool:
        """
        좋아요 토글
        return: True -> 좋아요 생성, False -> 좋아요 해제
        """
        post = await Post.get_or_none(id=post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        cache_key = CACHE_KEY_POST_LIKES.format(post_id=post_id)
        existing_like = await PostLike.get_or_none(user=self.user, post=post)

        if existing_like:
            # 좋아요 취소
            await existing_like.delete()
            # 캐시 감소
            likes_count = self.redis.get_value(cache_key)
            if likes_count is not None:
                self.redis.set_value(cache_key, likes_count - 1)
            return False
        else:
            # 좋아요 생성
            await PostLike.create(user=self.user, post=post)
            # 캐시 증가
            likes_count = self.redis.get_value(cache_key)
            if likes_count is not None:
                self.redis.set_value(cache_key, likes_count + 1)
            return True

    @atomic()
    async def create_post(
        self,
        title: str,
        body: str,
        tag_ids: Optional[List[int]] = None,
        images: Optional[List[UploadFile]] = None,
    ) -> Any:
        """
        게시물 생성 + 태그 + 이미지 업로드 예시
        이미지 최대 4장
        """
        if images and len(images) > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 4 images allowed",
            )

        post = await Post.create(
            title=title,
            body=body,
            writer=self.user,
        )

        # 태그 처리
        if tag_ids:
            # 1. 유효한 태그 ID들만 필터링
            existing_tags = await Tag.filter(id__in=tag_ids).all()

            if existing_tags:
                # 2. PostTag 객체 리스트 생성
                post_tags = [PostTag(post=post, tag=tag) for tag in existing_tags]

                # 3. 벌크 생성
                await PostTag.bulk_create(post_tags)

        # 이미지 업로드 처리
        if images:
            for image in images:
                folder = f"post/{post.id}/images"
                image_url = await s3_upload_file(folder, image)
                if image_url:
                    await PostImage.create(post=post, image=image_url)

        return post


class PostViewService:
    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user
        self.redis = RedisManager()

    async def _get_post_views(self, post_id: int, db_views: int) -> Any:
        """캐시된 조회수 조회"""
        cache_key = CACHE_KEY_POST_VIEWS.format(post_id=post_id)
        views_data = self.redis.get_value(cache_key)
        return views_data["count"] if views_data else db_views

    async def _get_post_likes(self, post_id: int) -> Any:
        """캐시된 좋아요 수 조회"""
        cache_key = CACHE_KEY_POST_LIKES.format(post_id=post_id)
        likes_count = self.redis.get_value(cache_key)
        if likes_count is None:
            likes_count = await PostLike.filter(post_id=post_id).count()
            self.redis.set_value(cache_key, likes_count, expire=CACHE_EXPIRE_TIME)
        return likes_count

    async def get_post_list(
        self, search: Optional[str] = None, page: int = 1, page_size: int = 10
    ) -> PostListResponse:
        """
        게시글 목록 조회 (페이징, 검색)
        검색 필터: title, body, tag__name
        """
        # 검색
        query = Q(is_active=True)
        if search:
            # title, body, tag_name 중 하나라도 검색어가 포함되면 필터
            query &= (
                Q(title__icontains=search)
                | Q(body__icontains=search)
                | Q(tags__name__icontains=search)
            )

        # 전체 개수
        total_count = await Post.filter(query).count()

        # 페이징 계산
        offset = (page - 1) * page_size

        # 쿼리 실행
        posts = (
            await Post.filter(query)
            .select_related("writer")
            .prefetch_related("images", "tags")
            .order_by("-id")
            .offset(offset)
            .limit(page_size)
        )

        # 5) 응답용 데이터 구성
        results = []
        for p in posts:
            tags = [TagInfo(id=pt.id, name=pt.name) for pt in p.tags]
            images = [img.image for img in p.images]
            results.append(
                PostListItemDto(
                    id=p.id,
                    title=p.title,
                    body=p.body,
                    tags=tags,
                    writer=UserSimpleProfile(
                        user_id=p.writer.id,
                        profile_picture=p.writer.profile_image or "",
                        name=p.writer.name,
                    ),
                    created_at=p.created_at.isoformat(),
                    images=images,
                    views=await self._get_post_views(p.id, p.views),
                    likes=await self._get_post_likes(p.id),
                )
            )
        return PostListResponse(
            total_count=total_count,
            results=results,
            page=page,
            page_size=page_size,
        )

    async def get_post_detail(self, post_id: int) -> PostDetailItemDto:
        """
        게시글 상세 조회
        - 조회수 증가 로직 (PostService.increment_view) 연동
        - 태그, 이미지, 작성자 등 prefetch
        """
        post = (
            await Post.get_or_none(id=post_id)
            .select_related("writer")
            .prefetch_related("images", "tags")
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # 조회수 증가
        post_service = PostService()
        await post_service.increment_view(post_id)

        # 관계된 Tag, Images 가져 오기
        tags = [TagInfo(id=tag.id, name=tag.name) for tag in post.tags]
        images = [img.image for img in post.images]

        return PostDetailItemDto(
            id=post.id,
            title=post.title,
            body=post.body,
            tags=tags,
            writer=UserSimpleProfile(
                user_id=post.writer.id,
                profile_picture=post.writer.profile_image or "",
                name=post.writer.name,
            ),
            created_at=post.created_at.isoformat(),
            images=images,
            views=await self._get_post_views(post.id, post.views),
            likes=await self._get_post_likes(post.id),
        )
