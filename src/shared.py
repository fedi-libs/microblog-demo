from typing import Optional
import uuid
import html
from urllib.parse import urlparse

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
                if bcrypt.checkpw(
                    password,
                    (
                        password_hashed
                        if isinstance(password_hashed, bytes)
                        else password_hashed.encode("utf-8")
                    ),
                ):
                    return True
                else:
                    return False
            else:
                return False


async def fetch_posts_with_post_id(db_path, post_id):
    async with aiosqlite.connect(db_path) as db:
        query = """
        SELECT Users.username, Users.host, Posts.content
        FROM Posts
        JOIN Users ON Posts.user_id = Users.id
        WHERE Posts.id = ?
        ORDER BY Posts.created_at DESC
        LIMIT 1
        """
        async with db.execute(query, (post_id,)) as cursor:
            results = await cursor.fetchall()
            if results:
                username, host, content = results[0]
                return {"username": username, "content": content, "host": host}
            return None


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
            return True, post_id
        else:
            return False, None


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
            SELECT u.url, u.shared_inbox, u.inbox, u.username, u.name, k.public_key, k.id, k.key_type, k.private_key, u.id
            FROM Users u
            LEFT JOIN Keys k ON u.id = k.user_id
            WHERE u.username = ? AND u.host IS NULL
            """,
                (username,),
            ) as cursor:
                user_info = await cursor.fetchall()

        if user_info:
            user_data = {
                "id": user_info[0][9],
                "url": user_info[0][0],
                "shared_inbox": user_info[0][1],
                "inbox": f"{SCHEME}://{HOST}" + user_info[0][2],
                "username": user_info[0][3],
                "name": user_info[0][4],
                "key": {
                    "public_key": user_info[0][5],
                    "private_key": user_info[0][8],
                    "id": user_info[0][6],
                    "key_type": user_info[0][7],
                },
            }

            return user_data
        else:
            return None


async def create_user(
    db_path: str,
    username: str,
    url: str,
    inbox: str,
    name: Optional[str] = None,
    shared_inbox: Optional[str] = None,
) -> str | None:
    async with aiosqlite.connect(db_path) as db:
        user = await fetch_user_info("microblog.db", username)

        if not user:
            url_parsed = urlparse(url)
            if url_parsed.hostname:
                id = str(uuid.uuid4())
                await db.execute(
                    """
                    INSERT INTO Users (id, username, host, name, password, url, inbox, shared_inbox)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        id,
                        username,
                        url_parsed.hostname,
                        name,
                        None,
                        url,
                        inbox,
                        shared_inbox,
                    ),
                )
                await db.commit()
                return id
        else:
            return user["id"]
    return None


async def follow_user(db_path, follower_id, followed_username, followed_host=None):
    async with aiosqlite.connect(db_path) as db:
        user = await fetch_user_info(db_path, followed_username, followed_host)
        if user:
            await db.execute(
                """
                        INSERT INTO Followers (follower_id, followed_id)
                        VALUES (?, ?)
                        """,
                (follower_id, user["id"]),
            )
            await db.commit()
            return True
    return False
