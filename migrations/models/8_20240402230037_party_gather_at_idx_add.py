from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` ADD INDEX `idx_parties_gather__f3eea5` (`gather_at`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `parties` DROP INDEX `idx_parties_gather__f3eea5`;"""
