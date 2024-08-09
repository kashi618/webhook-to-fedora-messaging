# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The values for any configuration variable that was not mentioned of in the
custom configuration file will be inherently taken from the default values
"""

import logging

from fastapi import FastAPI

from webhook_to_fedora_messaging.endpoints import message, service, user


logger = logging.getLogger(__name__)

desc = "Webhook To Fedora Messaging"

tags_metadata = [
    {"name": "messages", "description": "Operations on messages"},
    {"name": "services", "description": "Operations on services"},
    {"name": "users", "description": "Operations on users"},
]

PREFIX = "/api/v1"


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     setup_config()
#     setup_database_manager()
#     yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Webhook To Fedora Messaging",
        description=desc,
        contact={
            "name": "Fedora Infrastructure",
            "email": "infrastructure@lists.fedoraproject.org",
        },
        openapi_tags=tags_metadata,
        # lifespan=lifespan,
    )

    app.include_router(user.router, prefix=PREFIX)
    app.include_router(service.router, prefix=PREFIX)
    app.include_router(message.router, prefix=PREFIX)

    return app
