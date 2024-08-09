import logging
import os
from asyncio import run

import click

from webhook_to_fedora_messaging import __version__
from webhook_to_fedora_messaging.config import set_config_file
from webhook_to_fedora_messaging.database import get_db_manager, setup_database


logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "-c",
    "--conf",
    "conf",
    type=click.Path(exists=True),
    help="Read configuration from the specified module",
    default=None,
)
@click.version_option(version=__version__, prog_name="w2fm")
def main(conf=None):
    if conf:
        set_config_file(os.path.abspath(conf))
        get_db_manager.cache_clear()


@main.command(name="setup", help="Setup the database schema in the specified environment")
def setup():
    run(setup_database())
