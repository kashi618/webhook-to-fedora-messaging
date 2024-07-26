# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Use sqlalchemy-helpers.

Import the functions we will use in the main code and in migrations.
"""

from sqlalchemy_helpers import (  # noqa: F401
    Base,
    exists_in_db,
    get_or_create,
    is_sqlite,
    update_or_create,
)
from sqlalchemy_helpers.flask_ext import DatabaseExtension, first_or_404, get_or_404  # noqa: F401


db = DatabaseExtension()
