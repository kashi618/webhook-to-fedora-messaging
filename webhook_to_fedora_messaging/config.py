# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from functools import cache
from pathlib import Path

from pydantic import BaseModel, DirectoryPath, FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CONFIG_FILE = _config_file = os.getenv(
    "W2FM_CONFIG", "/etc/webhook-to-fedora-messaging/webhook-to-fedora-messaging.cfg"
)
TOP_DIR = Path(__file__).parent


class SQLAlchemyModel(BaseModel):
    model_config = SettingsConfigDict(extra="allow")

    url: str = f"sqlite:///{TOP_DIR.parent.joinpath('webhook-to-fedora-messaging.db').absolute()}"
    echo: bool = False


class AlembicModel(BaseModel):
    migrations_path: DirectoryPath = TOP_DIR.joinpath("migrations").absolute()


class DBModel(BaseModel):
    sqlalchemy: SQLAlchemyModel = SQLAlchemyModel()
    alembic: AlembicModel = AlembicModel()


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    database: DBModel = DBModel()
    fasjson_url: str = "https://fasjson.fedoraproject.org"
    logging_config: FilePath = "/etc/webhook-to-fedora-messaging/logging.yaml"


@cache
def get_config() -> Config:
    return Config(_env_file=_config_file)


def set_config_file(path: str) -> None:
    global _config_file
    _config_file = path
    get_config.cache_clear()
