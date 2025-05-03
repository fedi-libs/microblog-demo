from typing import Union

from apmodel import Create, Note
from fastapi import APIRouter, Form, Cookie, Request
from fastapi.responses import Response, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .shared import create_post, login_user, fetch_posts_with_post_id
from .broker import create_post as tasq_create_post
from . import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/posts/{id}")
async def show_post(request: Request, id: str):
    post = await fetch_posts_with_post_id("microblog.db", id)
    if not post:
        return Response(content="Not Found", status_code=404)
    if "application/activity+json" in request.headers.get("accept") or "application/ld+json" in request.headers.get("accept"):
        return JSONResponse(content=Note(
            id=f"{config.SCHEME}://{config.HOST}/posts/{id}",
            attributedTo=f"{config.SCHEME}://{config.HOST}/@{post['username']}",
            content=post["content"],
            to=["https://www.w3.org/ns/activitystreams#Public"],
        ).to_dict(), media_type="application/activity+json")
    return templates.TemplateResponse(
        request=request,
        name="post.html",
        context={
            "request": request,
            "post": post,
        },
    )


@router.get("/posts/{id}/activity")
async def post_activity(request: Request, id: str):
    post = await fetch_posts_with_post_id("microblog.db", id)
    if not post:
        return Response(content="Not Found", status_code=404)
    create = Create(
        id=f"{config.SCHEME}://{config.HOST}/posts/{id}/activity",
        actor=f"{config.SCHEME}://{config.HOST}/@{post['username']}",
        object=Note(
            id=f"{config.SCHEME}://{config.HOST}/posts/{id}",
            content=post["content"],
            to=["https://www.w3.org/ns/activitystreams#Public"],
        ),
    )
    return JSONResponse(
        content=create.to_dict(),
        media_type="application/activity+json"
    )


@router.post("/post/create")
async def post_create(
    content: str = Form(),
    username: Union[str, None] = Cookie(default=None),
    password: Union[str, None] = Cookie(default=None),
):
    if await login_user("microblog.db", username, password.encode("utf-8")):
        _, post_id = await create_post("microblog.db", username, content, host=None)
        await tasq_create_post.kiq(username=username, content=content, post_id=post_id)
        return RedirectResponse(url="/", status_code=303)
    else:
        response = Response(content="Forbidden", status_code=403)
        response.delete_cookie("username")
        response.delete_cookie("password")
        return response
