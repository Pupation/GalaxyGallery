import asyncio
import ipaddress

from utils.connection.nosql.db import client
from utils.cache import gg_cache
from models.helper import IP

from fastapi.logger import logger

@gg_cache
def _check_db(ip: int, version: int):
    ret = client.ip_blacklist.find_one({
        "lower": { "$lte" : ip },
        "higher": { "$gte": ip },
        "version": version
    })
    return ret is not None

def check_ip(ip: IP):
    """
        Check if a given ip is blacklisted.

        _ret_: Coroutine object. To get result, use `await` keyword.
            `True`: Hit in blacklist
            `False`: Not hit in blacklist

    """
    logger.debug("Checking ip: %s" % (str(IP)))
    return asyncio.create_task(_check_ip(ip))

async def _check_ip(ip: IP):
    ret = False
    if ip.has_ipv4():
        ipv4 = int(ipaddress.ip_address(ip.ipv4))
        ret = ret or _check_db(ipv4, 4)
    if ip.has_ipv6():
        ipv6 = int(ipaddress.ip_address(ip.ipv6)) >> 64 # for ipv6 addresses, we only check the first 64 bits
        ret = ret or _check_db(ipv6, 6)
    return ret

def flush_cache():
    _check_db.cache_clear()