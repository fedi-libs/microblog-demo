from typing import Union
from fastapi import APIRouter, Form, Cookie
from fastapi.responses import Response, RedirectResponse

from .shared import create_post, login_user

router = APIRouter()


@router.post("/post/create")
async def post_create(content: str = Form(), username: Union[str, None] = Cookie(default=None), password: Union[str, None] = Cookie(default=None)):
    if await login_user("microblog.db", username, password.encode("utf-8")):
        await create_post("microblog.db", username, content, host=None)
        return RedirectResponse(url="/", status_code=303)
    else:
        return Response(content="Forbidden", status_code=403)