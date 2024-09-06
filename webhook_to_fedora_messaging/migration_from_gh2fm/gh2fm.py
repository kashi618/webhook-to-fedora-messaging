from contextlib import asynccontextmanager

from sqlalchemy import Boolean, Column, ForeignKey, Integer, MetaData, String, Table, Unicode
from sqlalchemy.ext.asyncio import create_async_engine


metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("username", Unicode, primary_key=True),
    Column("github_username", Unicode),
    Column("emails", Unicode),
    Column("full_name", String),
    Column("oauth_access_token", Unicode),
)

repos = Table(
    "repos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", Unicode),
    Column("description", Unicode),
    Column("language", Unicode),
    Column("enabled", Boolean),
    Column("username", Unicode, ForeignKey("users.github_username")),
)

org_to_user = Table(
    "org_to_user_mapping",
    metadata,
    Column("org_id", Unicode, ForeignKey("users.github_username"), primary_key=True),
    Column("usr_id", Unicode, ForeignKey("users.github_username"), primary_key=True),
)


@asynccontextmanager
async def get_session(url):
    engine = create_async_engine(url)

    async with engine.begin() as conn:
        yield conn

    await engine.dispose()
