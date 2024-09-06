import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import click
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound

from webhook_to_fedora_messaging.config import set_config_file
from webhook_to_fedora_messaging.database import get_session
from webhook_to_fedora_messaging.migration_from_gh2fm import gh2fm
from webhook_to_fedora_messaging.models import Service, User
from webhook_to_fedora_messaging.models.owners import owners_table


log = logging.getLogger(__name__)


@click.command()
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=True, readable=True),
    help="Path to the configuration file",
)
@click.option(
    "-g",
    "--github2fedmsg-db-url",
    envvar="GITHUB2FEDMSG_DB_URL",
    required=True,
    help="The URL to Github2Fedmsg's DB",
)
@click.option("-d", "--debug", is_flag=True, help="Show more information")
@click.argument("fas_username", required=True)
@click.argument("repo", required=True)
def main(config_path, github2fedmsg_db_url, debug, fas_username, repo):
    if config_path:
        set_config_file(config_path)
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO
    )
    if debug:
        log.setLevel(logging.DEBUG)
        log.addHandler(log.root.handlers[0])
        log.propagate = False

    if repo.count("/") != 1:
        raise click.BadArgumentUsage(
            "The repo argument must be in the 'user_or_org/repo_name' format."
        )
    asyncio.run(_main(repo, fas_username, github2fedmsg_db_url))


with_db_session = asynccontextmanager(get_session)


async def _main(repo_full_name, fas_username, github2fedmsg_db_url):
    user_or_org, repo_name = repo_full_name.split("/")
    async with gh2fm.get_session(github2fedmsg_db_url) as gh2fm_session:
        query = (
            select(gh2fm.repos, gh2fm.users.c.username.label("fas_username"))
            .join_from(gh2fm.repos, gh2fm.users)
            .where(gh2fm.repos.c.username == user_or_org, gh2fm.repos.c.name == repo_name)
        )
        result = await gh2fm_session.execute(query)
        try:
            repo = result.one()
        except NoResultFound:
            log.error("Could not find repo %r in Github2Fedmsg's database", repo_full_name)
            return
        if not repo.enabled:
            log.info("The repo is disabled, skipping.")
            return
        if not repo.fas_username.startswith("github_org_") and repo.fas_username != fas_username:
            log.warning(
                "The repo %s used to be linked to FAS user %s, it will now be linked "
                "to FAS user %s",
                repo_full_name,
                repo.fas_username,
                fas_username,
            )
        async with with_db_session() as db_session:
            await import_repo(db_session, repo, fas_username)


async def import_repo(db, repo, username):
    db_user = await db.scalar(select(User).where(User.name == username))
    if not db_user:
        db_user = User(name=username)
        db.add(db_user)
        log.debug("Adding user %s", username)
        await db.flush()
    db_service = Service(
        name=f"{repo.username}/{repo.name}",
        uuid=uuid4().hex[0:8],
        type="github",
        desc=f"Migrated from GitHub2FedMsg. {repo.description}",
        disabled=False,
    )
    db.add(db_service)
    try:
        await db.flush()
    except IntegrityError:
        log.warning("Service already exists.")
        await db.rollback()
        return
    stmt = owners_table.insert().values({"service_id": db_service.id, "user_id": db_user.id})
    await db.execute(stmt)
    log.info("Service %s created", db_service.name)


if __name__ == "__main__":
    main()
