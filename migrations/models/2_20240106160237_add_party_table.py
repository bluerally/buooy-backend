from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `parties` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `title` VARCHAR(255),
    `body` LONGTEXT,
    `gather_at` DATETIME(6)   COMMENT '모임 날짜',
    `due_at` DATETIME(6)   COMMENT '마감 날짜',
    `place_id` BIGINT,
    `place_name` VARCHAR(255),
    `address` VARCHAR(255),
    `longitude` DOUBLE,
    `latitude` DOUBLE,
    `participant_limit` INT   DEFAULT 0,
    `participant_cost` INT   DEFAULT 0,
    `is_active` BOOL   DEFAULT 1,
    `organizer_user_id` INT,
    `sport_id` INT,
    CONSTRAINT `fk_parties_users_95f730ff` FOREIGN KEY (`organizer_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_parties_sports_78d4a37a` FOREIGN KEY (`sport_id`) REFERENCES `sports` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `party_participants` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `status` SMALLINT NOT NULL  COMMENT 'PENDING: 0\nAPPROVED: 1\nREJECTED: 2\nCANCELLED: 3' DEFAULT 0,
    `participant_user_id` INT,
    `party_id` INT,
    CONSTRAINT `fk_party_pa_users_0de8a279` FOREIGN KEY (`participant_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_party_pa_parties_01121cac` FOREIGN KEY (`party_id`) REFERENCES `parties` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE `models.PartyParticipant` (
    `user_id` INT NOT NULL REFERENCES `users` (`id`) ON DELETE CASCADE,
    `parties_id` INT NOT NULL REFERENCES `parties` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `models.PartyParticipant`;
        DROP TABLE IF EXISTS `parties`;
        DROP TABLE IF EXISTS `party_participants`;"""
