import logging
import logging.config
import os
from asyncio import run

import click
import yaml
from sqlalchemy_helpers.aio import SyncResult

from webhook_to_fedora_messaging import __version__
from webhook_to_fedora_messaging.config import get_config, set_config_file
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
    config = get_config()
    with open(config.logging_config) as fh:
        logging.config.dictConfig(yaml.safe_load(fh))


@main.command(name="setup", help="Setup the database schema in the specified environment")
def setup():
    result = run(setup_database())
    if result == SyncResult.ALREADY_UP_TO_DATE:
        click.echo("The database was already up-to-date")
    elif result == SyncResult.CREATED:
        click.echo("The database has been created")
    elif result == SyncResult.UPGRADED:
        click.echo("The database has been upgraded")
