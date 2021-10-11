import asyncio
import ipaddress

from functools import lru_cache

from utils.connection.nosql.db import client

from fastapi.logger import logger

@lru_cache(maxsize = None)
def _check_db(ip: str, version: int):
    ret = client.ip_blacklist.find_one({
        "lower": { "$lte" : ip },
        "higher": { "$gte": ip },
        "version": version
    })
    return ret is not None

def check_ip(ip: str, version: int = 4):
    """
        Check if a given ip is blacklisted.

        _ret_: Coroutine object. To get result, use `await` keyword.

    """
    logger.debug("Checking ip: %s, version: %d" % (ip, version))
    print("Checking ip: %s, version: %d" % (ip, version))
    if version == 4:
        return asyncio.create_task(_check_ip4(ip))
    if version == 6:
        return asyncio.create_task(_check_ip6(ip))

async def _check_ip4(ip: str):
    ip = int(ipaddress.ip_address(ip))
    return _check_db(ip, 4)

async def _check_ip6(ip: str):
    ip = int(ipaddress.ip_address(ip))
    return _check_db(ip, 6)
