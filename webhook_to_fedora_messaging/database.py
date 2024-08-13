# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Use sqlalchemy-helpers.

Import the functions we will use in the main code and in migrations.
"""

from collections.abc import AsyncIterator
from functools import cache

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_helpers.aio import (  # noqa: F401
    Base,
    get_or_create,
    update_or_create,
)
from sqlalchemy_helpers.fastapi import AsyncDatabaseManager, make_db_session

from .config import get_config


@cache
def get_db_manager():
    config = get_config()
    return AsyncDatabaseManager(
        config.database.sqlalchemy.url,
        config.database.alembic.migrations_path.as_posix(),
        # engine_args={"echo": True},
    )


async def setup_database():
    db = get_db_manager()
    # Populate Base.metadata
    from . import models  # noqa: F401

    return await db.sync()


async def get_session() -> AsyncIterator[AsyncSession]:
    db = get_db_manager()
    async for session in make_db_session(db):
        yield session
