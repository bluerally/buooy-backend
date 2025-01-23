from common.models import BaseModel
from tortoise import fields


class Post(BaseModel):
    title = fields.CharField(null=True, blank=True, max_length=255)
    body = fields.TextField(null=True, blank=True)
    writer = fields.ForeignKeyField(
        "models.User", related_name="posts", null=True, on_delete=fields.SET_NULL
    )
    views = fields.BigIntField(default=0)
    is_active = fields.BooleanField(null=True, default=True)
    tags = fields.ManyToManyField(
        "models.Tag",
        related_name="posts",
        through="post_tags",
        forward_key="tag_id",
        backward_key="post_id",
    )

    class Meta:
        table = "posts"

    def __str__(self) -> str:
        return f"{self.id} - {self.title}"


class PostLike(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    post = fields.ForeignKeyField(
        "models.Post", null=True, on_delete=fields.SET_NULL, related_name="likes"
    )

    class Meta:
        table = "post_likes"


class PostImage(BaseModel):
    post = fields.ForeignKeyField(
        "models.Post", null=True, on_delete=fields.SET_NULL, related_name="images"
    )
    image = fields.CharField(null=True, blank=True, max_length=255)

    class Meta:
        table = "post_images"


class Tag(BaseModel):
    name = fields.CharField(null=True, blank=True, max_length=255)

    class Meta:
        table = "tags"


class PostTag(BaseModel):
    tag = fields.ForeignKeyField("models.Tag", null=True, on_delete=fields.SET_NULL)
    post = fields.ForeignKeyField("models.Post", null=True, on_delete=fields.SET_NULL)

    class Meta:
        table = "post_tags"


class PostComment(BaseModel):
    post = fields.ForeignKeyField(
        "models.Post", null=True, on_delete=fields.SET_NULL, related_name="comments"
    )
    writer = fields.ForeignKeyField(
        "models.User",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="post_comments",
    )
    content = fields.TextField(null=True, blank=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "post_comments"


class PostCommentLike(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    comment = fields.ForeignKeyField(
        "models.PostComment", null=True, on_delete=fields.SET_NULL, related_name="likes"
    )

    class Meta:
        table = "post_comment_likes"


class PostCommentReply(BaseModel):
    parent_comment = fields.ForeignKeyField(
        "models.PostComment",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="replies",
    )
    writer = fields.ForeignKeyField(
        "models.User",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="post_comment_replies",
    )
    content = fields.TextField(null=True, blank=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "post_comment_reply"


class PostCommentReplyLike(BaseModel):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    comment = fields.ForeignKeyField(
        "models.PostCommentReply",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="likes",
    )

    class Meta:
        table = "post_comment_reply_likes"
