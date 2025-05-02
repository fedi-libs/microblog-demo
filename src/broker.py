from apkit import ApRequest
from apmodel import Create, Note
from taskiq import InMemoryBroker
from cryptography.hazmat.primitives import serialization

from .shared import fetch_user_info
from . import config

broker = InMemoryBroker()

@broker.task
async def create_post(username: str, content: str, post_id: str):
    user = await fetch_user_info("microblog.db", username)
    if user:
        create = Create(
            id=f"{config.SCHEME}://{config.HOST}/posts/{post_id}",
            actor=user["url"],
            object=Note(
                id=f"{config.SCHEME}://{config.HOST}/posts/{post_id}",
                content=content,
                to=["https://www.w3.org/ns/activitystreams#Public"],
            ),
        )
        priv_key = serialization.load_pem_private_key(
            user["key"]["private_key"].encode("utf-8"),
            password=None,
        )
        async with ApRequest(key_id=user["key"]["id"], private_key=priv_key) as req:
            resp = await req.signed_post(
                url="",
                data=create.to_dict(),
                headers={"Content-Type": "application/activity+json", "User-Agent": "microblog-demo/0.1.0"},
            )
            print("---")
            print(resp.status)
            print(await resp.text())