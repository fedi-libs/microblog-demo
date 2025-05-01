from typing import Union

from fastapi import Cookie, FastAPI, Request
from fastapi.templating import Jinja2Templates

from . import setup, shared, db_setup, post

db_setup.run_setup()
app = FastAPI()
app.include_router(setup.router)
app.include_router(post.router)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request, username: Union[str, None] = Cookie(default=None), password: Union[str, None] = Cookie(default=None)):
    if await shared.check_users_found("microblog.db"):
        if username and password:
            if shared.login_user("microblog.db", username, password.encode("utf-8")):
                return templates.TemplateResponse(
                    request=request, name="home.html", context={"request": request, "posts": await shared.fetch_posts_with_usernames("microblog.db")}
                )
        else:
            return templates.TemplateResponse(
                request=request, name="login.html"
            )
    else:
        return templates.TemplateResponse(
            request=request, name="setup.html"
        )
