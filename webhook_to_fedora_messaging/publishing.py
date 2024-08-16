import asyncio
import logging
import sys
import traceback

import backoff
from fedora_messaging import api
from fedora_messaging import exceptions as fm_exceptions


log = logging.getLogger(__name__)


def backoff_hdlr(details):
    log.warning("Publishing message failed. Retrying. %s", traceback.format_tb(sys.exc_info()[2]))


def giveup_hdlr(details):
    log.error("Publishing message failed. Giving up. %s", traceback.format_tb(sys.exc_info()[2]))


@backoff.on_exception(
    backoff.expo,
    (fm_exceptions.ConnectionException, fm_exceptions.PublishException),
    max_tries=3,
    on_backoff=backoff_hdlr,
    on_giveup=giveup_hdlr,
)
async def publish(message):
    deferred = api.twisted_publish(message)
    loop = asyncio.get_running_loop()
    await deferred.asFuture(loop)
