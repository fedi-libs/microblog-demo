from contextlib import asynccontextmanager
from typing import Union

from apkit import APKit
from apkit.webfinger import Resource as WebFingerResource
from apkit.x.starlette import ActivityPubMiddleware
from apmodel import Person, Follow
from apmodel.security.cryptographickey import CryptographicKey
from fastapi import Cookie, FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import setup, shared, db_setup, post, config
from .broker import broker

db_setup.run_setup()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.startup()
    yield
    await broker.shutdown()

app = FastAPI(lifespan=lifespan)
ap = APKit(
    name="Microblog",
    description="A simple microblogging demo",
)
app.include_router(setup.router)
app.include_router(post.router)
app.add_middleware(ActivityPubMiddleware, apkit=ap)
templates = Jinja2Templates(directory="templates")

@ap.on(Follow)
async def on_follow(request, follow: Follow):
    pass

@ap.webfinger()
async def webfinger(request: Request, resource: WebFingerResource):
    if config.HOST != resource.host:
        return Response(content="Not Found", status_code=404)
    user = await shared.fetch_user_info("microblog.db", resource.username)
    if user:
        return JSONResponse(
            content={
                "subject": resource.to_string(),
                "aliases": [f"{config.SCHEME}://{config.HOST}/@{resource.username}"],
                "links": [
                    {
                        "rel": "self",
                        "type": "application/activity+json",
                        "href": f"{config.SCHEME}://{config.HOST}/@{resource.username}",
                    }
                ],
            },
            media_type="application/jrd+json",
        )
    return Response(content="Not Found", status_code=404)


@app.get("/@{username}")
async def user(request: Request, username: str):
    user = await shared.fetch_user_info("microblog.db", username)
    if user:
        actor = Person(
            id=f"{config.SCHEME}://{config.HOST}/@{user['username']}",
            name=user["name"] if user.get("name") else user["username"],
            preferredUsername=user["username"],
            inbox=user["inbox"] if user.get("inbox") else None,
            sharedInbox=user["shared_inbox"],
            url=user["url"] if user.get("url") else None,
            publicKey=CryptographicKey(
                id=user["key"]["id"],
                owner=f"{config.SCHEME}://{config.HOST}/@{user['username']}",
                publicKeyPem=user["key"]["public_key"],
            ),
        )
        return JSONResponse(
            content=actor.to_dict(), media_type="application/activity+json"
        )
    return Response(content="Not Found", status_code=404)


@app.get("/")
async def index(
    request: Request,
    username: Union[str, None] = Cookie(default=None),
    password: Union[str, None] = Cookie(default=None),
):
    if await shared.check_users_found("microblog.db"):
        if username and password:
            if await shared.login_user(
                "microblog.db", username, password.encode("utf-8")
            ):
                return templates.TemplateResponse(
                    request=request,
                    name="home.html",
                    context={
                        "request": request,
                        "posts": await shared.fetch_posts_with_usernames(
                            "microblog.db"
                        ),
                    },
                )
            else:
                response = RedirectResponse("/")
                response.delete_cookie("username")
                response.delete_cookie("password")
                return response
        else:
            return templates.TemplateResponse(request=request, name="login.html")
    else:
        return templates.TemplateResponse(request=request, name="setup.html")
