# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later


from datetime import datetime, UTC
from functools import partial
from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP


class UUIDCreatableMixin:
    """
    An SQLAlchemy mixin to automatically generate a custom 8-digit UUID string
    """

    uuid: Mapped[str] = mapped_column(unique=True, default=uuid4().hex[0:8])


class CreatableMixin:
    """
    An SQLAlchemy mixin to store the time when an entity was created
    """

    creation_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=partial(datetime.now, tz=UTC),
    )
