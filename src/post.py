from typing import Union
from fastapi import APIRouter, Form, Cookie
from fastapi.responses import Response, RedirectResponse

from .shared import create_post, login_user
from .broker import create_post as tasq_create_post

router = APIRouter()


@router.post("/post/create")
async def post_create(content: str = Form(), username: Union[str, None] = Cookie(default=None), password: Union[str, None] = Cookie(default=None)):
    if await login_user("microblog.db", username, password.encode("utf-8")):
        _, post_id = await create_post("microblog.db", username, content, host=None)
        await tasq_create_post.kiq(username=username, content=content, post_id=post_id)
        return RedirectResponse(url="/", status_code=303)
    else:
        return Response(content="Forbidden", status_code=403)