import asyncio
import logging
from contextlib import asynccontextmanager

import click
import gidgethub
import gidgethub.abc
import gidgethub.httpx
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from webhook_to_fedora_messaging.config import set_config_file
from webhook_to_fedora_messaging.database import get_session
from webhook_to_fedora_messaging.models import Service


DESC_PREFIX = "Migrated from GitHub2FedMsg."
ISSUE_TITLE = "Migration Requested from Github2Fedmsg to Webhook To Fedora Messaging"
ISSUE_BODY = """
Your project was listed in the Github2Fedmsg database and we reach out to you to inform you about
the upcoming deprecation of the service. As the Fedora Infrastructure is finishing up with
migrating its applications away from Fedmsg to Fedora Messaging, we encourage you to migrate your
repository to the successor of the Github2Fedmsg project, Webhook To Fedora Messaging.

Please follow this $LINK to the official announcement of the project's release and use the
instructions there to migrate to the new service. If this notification was a mistake, please close
this ticket. We will not act on the repositories for which no migration has been requested
and any related Github2Fedmsg operations will stop working once the service is decommissioned.
"""

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
    "-u",
    "--github-username",
    envvar="GITHUB_USERNAME",
    help="The Github username that will be opening the issues",
)
@click.option("-t", "--github-token", envvar="GITHUB_TOKEN", help="The Github API token")
@click.option("-d", "--debug", is_flag=True, help="Show more information")
def main(config_path, github_username, github_token, debug):
    if config_path:
        set_config_file(config_path)
    logging.basicConfig(
        format="%(asctime)s %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.INFO if debug else logging.WARNING)
    asyncio.run(_main(github_username, github_token))


with_db_session = asynccontextmanager(get_session)


async def _main(github_username, github_token):
    async with httpx.AsyncClient() as http_client:
        gh = gidgethub.httpx.GitHubAPI(http_client, github_username, oauth_token=github_token)
        query = (
            select(Service)
            .where(Service.disabled.is_(False), Service.desc.like(f"{DESC_PREFIX}%"))
            .options(selectinload(Service.users))
        )
        async with with_db_session() as db_session:
            for service in await db_session.scalars(query):
                await process_service(service, gh)


async def process_service(service, gh: gidgethub.abc.GitHubAPI):
    log.debug("Processing %s", service.name)
    issues_url = f"/repos/{service.name}/issues"
    issues = gh.getiter(issues_url, dict(state="all", creator=gh.requester))
    async for issue in issues:
        if issue["title"] == ISSUE_TITLE:
            return  # The issue already exists in this repo
    log.info("Creating issue in %s", service.name)
    new_issue = await gh.post(issues_url, data={"title": ISSUE_TITLE, "body": ISSUE_BODY})
    log.debug(
        "Created issue %s in %s (%s)", new_issue["number"], service.name, new_issue["html_url"]
    )


if __name__ == "__main__":
    main()
