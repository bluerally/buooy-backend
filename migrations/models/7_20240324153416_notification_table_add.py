from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `notifications` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `type` VARCHAR(100),
    `related_id` BIGINT,
    `message` LONGTEXT,
    `is_global` BOOL NOT NULL  DEFAULT 0,
    `target_user_id` INT,
    CONSTRAINT `fk_notifica_users_84552372` FOREIGN KEY (`target_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `notifications_read` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `notification_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_notifica_notifica_0199ac00` FOREIGN KEY (`notification_id`) REFERENCES `notifications` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_notifica_users_d76a3232` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `notifications`;
        DROP TABLE IF EXISTS `notifications_read`;"""
