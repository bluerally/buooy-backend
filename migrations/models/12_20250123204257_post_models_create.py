from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `posts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `title` VARCHAR(255),
    `body` LONGTEXT,
    `views` BIGINT NOT NULL  DEFAULT 0,
    `is_active` BOOL   DEFAULT 1,
    `writer_id` INT,
    CONSTRAINT `fk_posts_users_a5dd5af5` FOREIGN KEY (`writer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_comments` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `content` LONGTEXT,
    `is_active` BOOL NOT NULL  DEFAULT 1,
    `post_id` INT,
    `writer_id` INT,
    CONSTRAINT `fk_post_com_posts_08c5981e` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_com_users_a9da667b` FOREIGN KEY (`writer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_comment_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `comment_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_post_com_post_com_481944de` FOREIGN KEY (`comment_id`) REFERENCES `post_comments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_com_users_2ba45fc4` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_comment_reply` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `content` LONGTEXT,
    `is_active` BOOL NOT NULL  DEFAULT 1,
    `parent_comment_id` INT,
    `writer_id` INT,
    CONSTRAINT `fk_post_com_post_com_bbb4a506` FOREIGN KEY (`parent_comment_id`) REFERENCES `post_comments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_com_users_96708ff5` FOREIGN KEY (`writer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_comment_reply_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `comment_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_post_com_post_com_eccb587d` FOREIGN KEY (`comment_id`) REFERENCES `post_comment_reply` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_com_users_f3848567` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_images` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `image` VARCHAR(255),
    `post_id` INT,
    CONSTRAINT `fk_post_ima_posts_16fce689` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_likes` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `post_id` INT,
    `user_id` INT,
    CONSTRAINT `fk_post_lik_posts_b7ace4f6` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_lik_users_c2a724fd` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `tags` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `post_tags` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `post_id` INT,
    `tag_id` INT,
    CONSTRAINT `fk_post_tag_posts_f4cf39e6` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_post_tag_tags_ef69acfd` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `posts`;
        DROP TABLE IF EXISTS `post_comments`;
        DROP TABLE IF EXISTS `post_comment_likes`;
        DROP TABLE IF EXISTS `post_comment_reply`;
        DROP TABLE IF EXISTS `post_comment_reply_likes`;
        DROP TABLE IF EXISTS `post_images`;
        DROP TABLE IF EXISTS `post_likes`;
        DROP TABLE IF EXISTS `post_tags`;
        DROP TABLE IF EXISTS `tags`;"""
