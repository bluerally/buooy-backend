from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `notifications` ALTER COLUMN `classification` SET DEFAULT '';
        CREATE TABLE IF NOT EXISTS `feedbacks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `content` LONGTEXT NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `notifications` ALTER COLUMN `classification` DROP DEFAULT;
        DROP TABLE IF EXISTS `feedbacks`;"""
