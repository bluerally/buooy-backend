from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` RENAME COLUMN `contact` TO `notice`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` RENAME COLUMN `notice` TO `contact`;"""
