import aiosqlite
import bcrypt
from fastapi import APIRouter, Form, Response
from fastapi.responses import RedirectResponse

from .shared import check_users_found, login_user

router = APIRouter()


@router.post("/setup/complete")
async def setup_complete(username: str = Form(), password: str = Form()):
    is_user_found = await check_users_found("microblog.db")
    if is_user_found:
        return Response(status_code=500, content="Setup Failed; User already exists")
    else:
        async with aiosqlite.connect("microblog.db") as db:
            password = password.encode("utf-8")
            salt =  bcrypt.gensalt(rounds=12, prefix=b'2b')
            hashed = bcrypt.hashpw(password, salt)
            await db.execute(
                """
                        INSERT INTO Users (username, name, password, url, uri, inbox, shared_inbox)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                (
                    username,
                    username,
                    hashed,
                    f"/@{username}",
                    f"/@{username}",
                    "/inbox",
                    None,
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
