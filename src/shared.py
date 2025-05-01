import uuid
import html

import aiosqlite
import bcrypt

from .config import HOST, SCHEME


async def check_users_found(db_path):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT * FROM Users WHERE password IS NOT NULL"
        ) as cursor:
            results = await cursor.fetchall()
            if results:
                return True
            else:
                return False


async def login_user(db_path, username: str, password: bytes):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT username, password FROM Users WHERE username = ? AND host IS NULL",
            (username,),
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                username, password_hashed = result
                if bcrypt.checkpw(password, password_hashed):
                    return True
                else:
                    return False
            else:
                return False


async def fetch_posts_with_usernames(db_path):
    async with aiosqlite.connect(db_path) as db:
        query = """
        SELECT Users.username, Users.host, Posts.content
        FROM Posts
        JOIN Users ON Posts.user_id = Users.id
        ORDER BY Posts.created_at DESC
        LIMIT 10
        """
        async with db.execute(query) as cursor:
            results = await cursor.fetchall()
            posts = [
                {"username": username, "content": content, "host": host}
                for username, host, content in results
            ]
            return posts


async def create_post(db_path, username, content, host=None):
    async with aiosqlite.connect(db_path) as db:
        if host:
            async with db.execute(
                "SELECT id FROM Users WHERE username = ? AND host = ?", (username, host)
            ) as cursor:
                user = await cursor.fetchone()
        else:
            async with db.execute(
                "SELECT id FROM Users WHERE username = ? AND host IS NULL", (username,)
            ) as cursor:
                user = await cursor.fetchone()
        if user:
            user_id = user[0]
            post_id = str(uuid.uuid4())
            content = html.escape(content)

            url = f"{SCHEME}://{HOST}/posts/{post_id}"

            await db.execute(
                """
            INSERT INTO Posts (id, user_id, content, url)
            VALUES (?, ?, ?, ?)
            """,
                (post_id, user_id, content, url),
            )

            await db.commit()
            return True
        else:
            return False


async def fetch_user_info(db_path, username, host=None):
    async with aiosqlite.connect(db_path) as db:
        if host:
            async with db.execute(
                """
            SELECT u.url, u.shared_inbox, u.inbox, u.username, u.name, k.public_key, k.id, k.key_type
            FROM Users u
            LEFT JOIN Keys k ON u.id = k.user_id
            WHERE u.username = ? AND u.host = ?
            """,
                (username, host),
            ) as cursor:
                user_info = await cursor.fetchall()
        else:
            async with db.execute(
                """
            SELECT u.url, u.shared_inbox, u.inbox, u.username, u.name, k.public_key, k.id, k.key_type
            FROM Users u
            LEFT JOIN Keys k ON u.id = k.user_id
            WHERE u.username = ? AND u.host IS NULL
            """,
                (username,),
            ) as cursor:
                user_info = await cursor.fetchall()

        if user_info:
            user_data = {
                "url": user_info[0][0],
                "shared_inbox": user_info[0][1],
                "inbox": f"{SCHEME}://{HOST}" + user_info[0][2],
                "username": user_info[0][3],
                "name": user_info[0][4],
                "key": {
                    "public_key": user_info[0][5],
                    "id": user_info[0][6],
                    "key_type": user_info[0][7],
                },
            }

            return user_data
        else:
            return None