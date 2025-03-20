import asyncio
import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from uuid import uuid4

import click
from fasjson_client import Client as FasjsonClient
from fasjson_client.errors import APIError as FasjsonApiError
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
@click.argument("repo", required=True)
@click.argument("fas_username", required=False)
def main(config_path, github2fedmsg_db_url, debug, repo, fas_username):
    if config_path:
        set_config_file(config_path)
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s: %(message)s", level=logging.INFO
    )
    if debug:
        log.setLevel(logging.DEBUG)
        log.addHandler(log.root.handlers[0])
        log.propagate = False

    asyncio.run(_main(repo, fas_username, github2fedmsg_db_url))


with_db_session = asynccontextmanager(get_session)


async def _main(repo_full_name, fas_username, github2fedmsg_db_url):
    if "/" in repo_full_name:
        user_or_org, repo_name = repo_full_name.split("/")
    else:
        user_or_org, repo_name = repo_full_name, None
    query = (
        select(gh2fm.repos, gh2fm.users.c.username.label("fas_username"))
        .join_from(gh2fm.repos, gh2fm.users)
        .where(gh2fm.repos.c.username == user_or_org)
    )
    if repo_name is not None:
        query = query.where(gh2fm.repos.c.name == repo_name)
    else:
        query = query.where(gh2fm.repos.c.enabled.is_(True))

    async with gh2fm.get_session(github2fedmsg_db_url) as gh2fm_session:
        result = await gh2fm_session.execute(query)
        try:
            if repo_name is not None:
                repo = result.one()
            else:
                repo = result.first()
                if repo is None:
                    raise NoResultFound
        except NoResultFound:
            log.error("Could not find repo %r in Github2Fedmsg's database", repo_full_name)
            return
        if not repo.enabled:
            log.info("The repo %s/%s is disabled, skipping.", repo.username, repo.name)
            print(query)
            return
        original_fas_username = await _get_owner(gh2fm_session, repo)
        if not fas_username:
            fas_username = original_fas_username
        if original_fas_username != fas_username:
            log.warning(
                "The repo %s used to be linked to FAS user %s, it will now be linked "
                "to FAS user %s",
                repo_full_name,
                repo.fas_username,
                fas_username,
            )
        async with with_db_session() as db_session:
            await import_repo(db_session, repo_full_name, fas_username)


def _get_fasjson_url():
    from configparser import ConfigParser

    ipa_config = ConfigParser()
    ipa_config.read("/etc/ipa/default.conf")
    domain = ipa_config.get("global", "domain")
    return f"https://fasjson.{domain}"


async def _get_owner(gh2fm_session, repo):
    owner = repo.fas_username
    if owner.startswith("github_org_"):
        org_name = owner[len("github_org_") :]
        try:
            owner = (
                await gh2fm_session.execute(
                    select(gh2fm.users.c.username)
                    .join(
                        gh2fm.org_to_user,
                        gh2fm.org_to_user.c.org_id == gh2fm.users.c.github_username,
                    )
                    .where(gh2fm.org_to_user.c.usr_id == org_name)
                    .order_by(gh2fm.users.c.created_on)
                )
            ).scalar()
        except NoResultFound as e:
            log.error("No owner specified for github org %s", org_name)
            raise click.Abort() from e
    # Check that it actually exists
    return _get_fas_username(owner)


@lru_cache
def _get_fasjson_client():
    return FasjsonClient(_get_fasjson_url())


@lru_cache
def _get_fas_username(username):
    fasjson = _get_fasjson_client()
    try:
        fas_user = fasjson.get_user(username=username).result
    except FasjsonApiError as e:
        log.error("FASJSON error on user %s: %s", username, e)
        raise click.Abort() from e
    return fas_user["username"]


async def import_repo(db, repo_full_name, username, repo_description=""):
    db_user = await db.scalar(select(User).where(User.name == username))
    if not db_user:
        db_user = User(name=username)
        db.add(db_user)
        log.debug("Adding user %s", username)
        await db.flush()
    db_service = Service(
        name=f"{repo_full_name}",
        uuid=uuid4().hex[0:8],
        type="github",
        desc=f"Migrated from GitHub2FedMsg. {repo_description}".strip(),
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
    print(
        f"""Hi @{username} !

You can now add the following webhook to the """
        f'{"repo" if "/" in repo_full_name else "organization"} '
        "mentioned above."
    )
    if "/" in repo_full_name:
        user_or_org, repo_name = repo_full_name.split("/")
        print(
            f"Note that you can also add the webhook at the organization level (`{user_or_org}`), "
            "which will make it active for all the organization's repos. I would suggest doing "
            "that to save some effort and automatically cover repos you may add in the future "
            "(make sure however than another teammate hasn't already added it)."
        )
    print(
        f"""
```
Webhook URL: https://webhook.fedoraproject.org/api/v1/messages/{db_service.uuid}
Secret: {db_service.token}
Webhook content-type: application/json
```

Please tell us if there are any issues! Thanks!
"""
    )


if __name__ == "__main__":
    main()
