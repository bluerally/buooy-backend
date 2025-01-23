import io
import pytest
from starlette import status
from httpx import AsyncClient

from common.dependencies import get_current_user
from community.service.post_service import PostViewService
from users.models import User
from community.models import (
    Post,
    PostLike,
    PostComment,
    PostCommentLike,
    PostCommentReply,
    PostCommentReplyLike,
    Tag,
    PostTag,
    PostImage,
)


@pytest.mark.asyncio
async def test_create_post_success(client: AsyncClient) -> None:
    """
    게시글 생성 성공 케이스
    (이미지 없이)
    """
    # 1) 유저 생성
    user = await User.create(
        name="testuser",
        email="testuser@example.com",
        sns_id="some-sns-id",
    )
    # 2) get_current_user 오버라이드
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 3) 요청 - form data 로 전달
    response = await client.post(
        "/api/community/post",
        data={
            "title": "Test Title",
            "body": "Test Body",
        },
    )

    # 4) 검증
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message"] == "Post created successfully"

    created_post = await Post.get_or_none(title="Test Title")
    assert created_post is not None
    assert created_post.body == "Test Body"
    assert created_post.writer_id == user.id

    # 5) 의존성 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_post_fail_too_many_images(client: AsyncClient) -> None:
    """
    이미지를 5개 넘게 올렸을 때 400 Bad Request 발생 예시
    """
    user = await User.create(name="testuser2", email="test2@example.com")
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 5개의 이미지를 넘기는 예시
    files = [
        # ("title", (None, "Too Many Images")),
        # ("body", (None, "Body test")),
        ("image", ("img1.png", io.BytesIO(b"fake_image1"), "image/png")),
        ("image", ("img2.png", io.BytesIO(b"fake_image2"), "image/png")),
        ("image", ("img3.png", io.BytesIO(b"fake_image3"), "image/png")),
        ("image", ("img4.png", io.BytesIO(b"fake_image4"), "image/png")),
        ("image", ("img5.png", io.BytesIO(b"fake_image5"), "image/png")),
    ]
    response = await client.post(
        "/api/community/post",
        data={
            "title": "Too Many Images",
            "body": "Body test",
        },
        files=files,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Maximum 4 images allowed"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_posts_list_success(client: AsyncClient) -> None:
    """
    게시글 목록 조회 (간단 예시: page=1, limit=10 기본)
    """
    user = await User.create(
        name="Lister", email="lister@example.com", profile_image="/path/to/image.png"
    )

    # 더미 Post 데이터 생성
    for i in range(3):
        await Post.create(title=f"Post {i}", body=f"Body {i}", writer=user)

    response = await client.get("/api/community/post")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # PostListResponse 구조에 맞춰 검증
    assert "total_count" in data
    assert "results" in data
    assert "page" in data
    assert "page_size" in data

    assert data["total_count"] == 3
    assert len(data["results"]) == 3
    # results 중 첫 번째 게시글의 title 검증
    assert data["results"][0]["title"] == "Post 2"


@pytest.mark.asyncio
async def test_get_post_detail_success(client: AsyncClient) -> None:
    """
    게시글 상세 조회 + 조회수 증가 테스트
    """
    user = await User.create(
        name="DetailUser",
        email="detail@example.com",
        profile_image="/path/to/image.png",
    )
    post = await Post.create(
        title="Detail Title", body="Detail Body", writer=user, views=5
    )
    await PostImage.create(post=post, image="/path/to/image.png")

    # PostService.increment_view 로직이 동작하면, 호출 후 views 캐싱 -> DB 반영
    response = await client.get(f"/api/community/post/{post.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 응답 내에서 likes_count, images, tags 등도 내려줄 수 있음
    assert data["id"] == post.id
    assert data["title"] == post.title
    # ...
    # 여기서는 상세 JSON 구조를 라우터 로직에 맞춰 검증

    # 조회수 증가 확인 (캐시 임계 도달 전에 DB에는 바로 안 올라갈 수도 있으므로 단순 응답 check)
    # 필요 시 Redis mock 을 통해 실제로 뽑아볼 수도 있음.


@pytest.mark.asyncio
async def test_get_post_detail_includes_tags_images_success(
    client: AsyncClient
) -> None:
    """
    게시글 상세 조회 시, 등록된 태그 리스트와 이미지 리스트도 함께 응답에 포함되는지 테스트.
    """
    # 1) 테스트 유저 생성
    user = await User.create(
        name="DetailTester",
        email="detail-tester@example.com",
        profile_image="/path/to/image.png",
    )
    # 2) 게시글 생성
    post = await Post.create(
        title="Post with tags and images", body="Post Body", writer=user, views=10
    )
    # 3) 태그 2개 생성 후, PostTag로 연결
    tag1 = await Tag.create(name="Sports")
    tag2 = await Tag.create(name="Diving")
    await PostTag.create(post=post, tag=tag1)
    await PostTag.create(post=post, tag=tag2)

    # 4) 이미지 2개 생성 (이미지는 실제 S3 업로드 대신, DB에 경로만 저장한다고 가정)
    await PostImage.create(post=post, image="https://bucket.s3/1.png")
    await PostImage.create(post=post, image="https://bucket.s3/2.png")

    # 5) 의존성 주입 오버라이드 (로그인 유저)
    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 6) 상세 조회 API 호출
    response = await client.get(f"/api/community/post/{post.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 7) 응답 데이터 검증
    #    예: 라우터에서 "tags": [...], "images": [...] 형태로 내려준다고 가정
    assert data["id"] == post.id
    assert data["title"] == "Post with tags and images"
    assert data["views"] >= 10  # 조회수 증가 로직(Redis) 때문에 최소 10 이상

    # 태그 목록 (예: ["Sports", "Diving"])
    assert "tags" in data
    print(f"data: {data}")
    assert len(data["tags"]) == 2

    # 이미지 목록 (예: ["https://bucket.s3/1.png", "https://bucket.s3/2.png"])
    assert "images" in data
    assert len(data["images"]) == 2
    assert "https://bucket.s3/1.png" in data["images"]
    assert "https://bucket.s3/2.png" in data["images"]

    # 8) 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_toggle_post_like_success(client: AsyncClient) -> None:
    """
    게시글 좋아요 토글(생성 -> 취소) 테스트
    """
    user = await User.create(
        name="LikeUser",
        email="likeuser@example.com",
        profile_image="/path/to/image.png",
    )
    post = await Post.create(title="Like Post", body="Like Body", writer=user)

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 1) 좋아요 생성
    response = await client.post(f"/api/community/post/{post.id}/like")
    assert response.status_code == status.HTTP_200_OK

    assert await PostLike.filter(post=post, user=user).exists() is True

    # 2) 좋아요 취소
    response = await client.post(f"/api/community/post/{post.id}/like")
    assert response.status_code == status.HTTP_200_OK
    assert await PostLike.filter(post=post, user=user).exists() is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_comment_success(client: AsyncClient) -> None:
    """
    댓글 작성 테스트
    """
    user = await User.create(
        name="Commenter",
        email="commenter@example.com",
        profile_image="/path/to/image.png",
    )
    post = await Post.create(title="Comment Post", body="Body", writer=user)

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(
        f"/api/community/post/{post.id}/comment",
        json={"content": "New Comment Content"},
    )
    assert response.status_code == status.HTTP_201_CREATED

    created_comment = await PostComment.first()
    assert created_comment is not None
    assert created_comment.content == "New Comment Content"
    assert created_comment.post_id == post.id
    assert created_comment.writer_id == user.id

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_comment_success(client: AsyncClient) -> None:
    """
    댓글 수정 테스트
    """
    user = await User.create(
        name="Commenter2",
        email="commenter2@example.com",
        profile_image="/path/to/image.png",
    )
    post = await Post.create(title="Comment Post2", body="Body2", writer=user)
    comment = await PostComment.create(post=post, writer=user, content="Old Content")

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.put(
        f"/api/community/comment/{comment.id}",
        json={"content": "Updated Content"},
    )
    assert response.status_code == status.HTTP_200_OK

    updated_comment = await PostComment.get_or_none(id=comment.id)
    assert updated_comment.content == "Updated Content"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_comment_success(client: AsyncClient) -> None:
    """
    댓글 삭제(비활성화) 테스트
    """
    user = await User.create(
        name="DelCommentUser",
        email="del@example.com",
        profile_image="/path/to/image.png",
    )
    post = await Post.create(title="Del Post", body="Del Body", writer=user)
    comment = await PostComment.create(post=post, writer=user, content="Delete me")

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.delete(f"/api/community/comment/{comment.id}")
    print(f"user_id: {user.id}, writer_id: {post.writer.id}")
    assert response.status_code == status.HTTP_200_OK

    await comment.refresh_from_db()
    assert comment.is_active is False  # 실제 라우터 로직에 따라 다를 수 있음

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_toggle_comment_like_success(client: AsyncClient) -> None:
    """
    댓글 좋아요 토글
    """
    user = await User.create(
        name="CLikeUser", email="click@example.com", profile_image="/path/to/image.png"
    )
    post = await Post.create(title="CLike Post", body="CLike Body", writer=user)
    comment = await PostComment.create(post=post, user=user, content="Like my comment")

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 1) 좋아요
    response = await client.post(f"/api/community/comment/{comment.id}/like")
    assert response.status_code == status.HTTP_200_OK
    assert await PostCommentLike.filter(comment=comment, user=user).exists() is True

    # 2) 좋아요 취소
    response = await client.post(f"/api/community/comment/{comment.id}/like")
    assert response.status_code == status.HTTP_200_OK
    assert await PostCommentLike.filter(comment=comment, user=user).exists() is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_reply_success(client: AsyncClient) -> None:
    """
    대댓글 작성 테스트
    """
    user = await User.create(
        name="ReplyUser", email="reply@example.com", profile_image="/path/to/image.png"
    )
    post = await Post.create(title="Reply Post", body="Reply Body", writer=user)
    comment = await PostComment.create(post=post, user=user, content="I am comment")

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(
        f"/api/community/comment/{comment.id}/reply",
        json={"content": "Reply content"},
    )
    assert response.status_code == status.HTTP_201_CREATED

    new_reply = await PostCommentReply.first()
    assert new_reply is not None
    assert new_reply.parent_comment_id == comment.id
    assert new_reply.writer_id == user.id
    assert new_reply.content == "Reply content"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_toggle_reply_like_success(client: AsyncClient) -> None:
    """
    대댓글 좋아요 토글
    """
    user = await User.create(
        name="RLikeUser", email="rlike@example.com", profile_image="/path/to/image.png"
    )
    post = await Post.create(title="RLike Post", body="RLike Body", writer=user)
    comment = await PostComment.create(
        post=post, user=user, content="Comment for reply"
    )
    reply = await PostCommentReply.create(
        parent_comment=comment, user=user, content="Hello reply"
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    # 1) 좋아요
    response = await client.post(f"/api/community/comment/reply/{reply.id}/like")
    assert response.status_code == status.HTTP_200_OK
    assert await PostCommentReplyLike.filter(comment=reply, user=user).exists() is True

    # 2) 좋아요 취소
    response = await client.post(f"/api/community/comment/reply/{reply.id}/like")
    assert response.status_code == status.HTTP_200_OK
    assert await PostCommentReplyLike.filter(comment=reply, user=user).exists() is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_post_list_success() -> None:
    user = await User.create(name="ServiceUser", profile_image="/path/to/image.png")

    # 게시글 3개 생성
    post1 = await Post.create(
        title="Hello World", body="Body1", writer=user, is_active=True
    )
    post2 = await Post.create(
        title="Python Tortoise", body="Body2", writer=user, is_active=True
    )
    post3 = await Post.create(
        title="Django Something", body="Body3", writer=user, is_active=True
    )

    # 태그 연결 (post2 -> 'Python', post3 -> 'Framework')
    tag_python = await Tag.create(name="Python")
    tag_framework = await Tag.create(name="Framework")
    await PostTag.create(post=post2, tag=tag_python)
    await PostTag.create(post=post3, tag=tag_framework)

    # 이미지 연결 (post1 -> img1, post2 -> img2)
    await PostImage.create(post=post1, image="http://image1.png")
    await PostImage.create(post=post2, image="http://image2.png")

    service = PostViewService(user=user)
    # 1) 전체 조회
    result_all = await service.get_post_list(page=1, page_size=10)
    assert result_all.total_count == 3
    assert len(result_all.results) == 3

    # 2) 검색: title/body "Hello"
    result_hello = await service.get_post_list(search="Hello")
    assert result_hello.total_count == 1
    assert result_hello.results[0].title == "Hello World"

    # 3) 검색: 태그 이름 "python"
    result_python_tag = await service.get_post_list(search="python")
    assert result_python_tag.total_count == 1
    # post2 만 나와야 함
    res_post2 = result_python_tag.results[0]
    assert res_post2.title == "Python Tortoise"
    assert res_post2.tags[0].name == "Python"

    # 4) Pagination
    await Post.create(title="Extra 1", body="Body x1", writer=user, is_active=True)
    await Post.create(title="Extra 2", body="Body x2", writer=user, is_active=True)
    # 이제 총 5개
    result_page2 = await service.get_post_list(page=2, page_size=2)
    assert result_page2.total_count == 5
    assert len(result_page2.results) == 2  # page2 => 2개


@pytest.mark.asyncio
async def test_update_reply_success(client: AsyncClient) -> None:
    user = await User.create(name="ReplyUpdater", profile_image="/path/to/image.png")
    post = await Post.create(title="ReplyTest", body="...", writer=user)
    comment = await PostComment.create(post=post, writer=user, content="Comment")
    reply = await PostCommentReply.create(
        parent_comment=comment, writer=user, content="Old reply"
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.put(
        f"/api/community/comment/reply/{reply.id}",
        json={"content": "Updated reply content"},
    )
    assert response.status_code == status.HTTP_200_OK

    await reply.refresh_from_db()
    assert reply.content == "Updated reply content"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_reply_success(client: AsyncClient) -> None:
    user = await User.create(name="ReplyDeleter", profile_image="/path/to/image.png")
    post = await Post.create(title="DelTest", body="...", writer=user)
    comment = await PostComment.create(post=post, writer=user, content="Comment")
    reply = await PostCommentReply.create(
        parent_comment=comment, writer=user, content="Will be deleted"
    )

    from main import app

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.delete(f"/api/community/comment/reply/{reply.id}")
    assert response.status_code == status.HTTP_200_OK

    await reply.refresh_from_db()
    assert reply.is_active is False  # 실제 로직에 따라 비활성화 처리

    app.dependency_overrides.clear()
