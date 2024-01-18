from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `party_comments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `content` LONGTEXT,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `commenter_id` INT,
    `party_id` INT,
    CONSTRAINT `fk_party_co_users_a9e5942b` FOREIGN KEY (`commenter_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_party_co_parties_08480edf` FOREIGN KEY (`party_id`) REFERENCES `parties` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `party_comments`;"""
