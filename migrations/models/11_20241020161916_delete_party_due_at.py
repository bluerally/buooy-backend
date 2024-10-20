from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` DROP COLUMN `due_at`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` ADD `due_at` DATETIME(6)   COMMENT '마감 날짜';"""
