# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

from os import environ
from pathlib import Path

import pytest
from sqlalchemy_helpers import get_or_create

from webhook_to_fedora_messaging.database import db
from webhook_to_fedora_messaging.main import create_app
from webhook_to_fedora_messaging.models.service import Service
from webhook_to_fedora_messaging.models.user import User


@pytest.fixture()
def client(tmp_path):
    test_dir = Path(__file__).parent
    environ["W2FM_APPCONFIG"] = test_dir.joinpath("data/test.toml").as_posix()
    config = {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path.as_posix()}/w2fm.db"}
    app = create_app(config)
    with app.app_context():
        db.manager.sync()
    return app.test_client()


@pytest.fixture()
def db_user(client):
    with client.application.app_context():
        # Setup code to create the object in the database
        user, is_created = get_or_create(
            db.session, User, username="mehmet"
        )  # Adjust fields as necessary
        db.session.commit()

    yield user

    with client.application.app_context():
        # Teardown code to remove the object from the database
        db.session.query(User).filter_by(username="mehmet").delete()
        db.session.commit()


@pytest.fixture()
def db_service(client):
    with client.application.app_context():
        # Setup code to create the object in the database
        user, created = get_or_create(
            db.session, User, username="mehmet"
        )  # Adjust fields as necessary

        service, created = get_or_create(
            db.session,
            Service,
            name="GitHub Demo",
            type="GitHub",
            desc="description",
            user_id=user.id,
        )

        service.token = "dummy-service-token"  # noqa: S105
        db.session.commit()
        db.session.refresh(service)

    yield service

    with client.application.app_context():
        # Teardown code to remove the object from the database
        db.session.query(User).filter_by(username="mehmet").delete()
        db.session.query(Service).filter_by(name="GitHub Demo").delete()
        db.session.commit()
