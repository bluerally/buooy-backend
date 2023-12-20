from getpass import getpass

import bcrypt
from tortoise import Tortoise, run_async

from common.config import TORTOISE_ORM
from users.models import AdminUser


async def init():
    # Tortoise ORM을 초기화합니다.
    await Tortoise.init(config=TORTOISE_ORM)


async def create_admin_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    await AdminUser.create(username=username, password=hashed_password.decode())


async def main():
    while True:
        username = input("Enter admin username (or 'exit' to quit): ")
        if username == "exit":
            break
        password = getpass("Enter password for admin user: ")
        await create_admin_user(username, password)
        print(f"Admin user '{username}' created.")


if __name__ == "__main__":
    run_async(main())
