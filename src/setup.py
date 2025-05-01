import uuid

import aiosqlite
import bcrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import APIRouter, Form, Response
from fastapi.responses import RedirectResponse

from .shared import check_users_found, login_user
from .config import HOST, SCHEME

router = APIRouter()


@router.post("/setup/complete")
async def setup_complete(username: str = Form(), password: str = Form()):
    is_user_found = await check_users_found("microblog.db")
    if is_user_found:
        return Response(status_code=500, content="Setup Failed; User already exists")
    else:
        async with aiosqlite.connect("microblog.db") as db:
            user_id = str(uuid.uuid4())
            password = password.encode("utf-8")
            salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
            hashed = bcrypt.hashpw(password, salt)
            await db.execute(
                """
                        INSERT INTO Users (id, username, name, password, url, inbox, shared_inbox)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                (
                    user_id,
                    username,
                    username,
                    hashed,
                    f"{SCHEME}://{HOST}/@{username}",
                    "/inbox",
                    None,
                ),
            )
            priv = rsa.generate_private_key(
                key_size=3072, public_exponent=65537, backend=default_backend()
            )
            await db.execute(
                """
                INSERT INTO Keys (id, user_id, public_key, private_key, key_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"{SCHEME}://{HOST}/@{username}#main-key",
                    user_id,
                    priv.public_key().public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    ).decode("utf-8"),
                    priv.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    ).decode("utf-8"),
                    "RSASSA-PKCS1-v1_5",
                ),
            )
            await db.commit()
        return Response(
            status_code=200, content="Setup Complete! Login from the Root page!"
        )


@router.post("/login")
async def login(username: str = Form(), password: str = Form()):
    is_user_found = await check_users_found("microblog.db")
    if is_user_found:
        if await login_user("microblog.db", username, password.encode("utf-8")):
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="username", value=username, samesite="strict")
            response.set_cookie(key="password", value=password, samesite="strict")
            return response
        else:
            return Response(
                status_code=401, content="Login Failed; Incorrect username or password"
            )
    else:
        return RedirectResponse(url="/setup", status_code=303)
