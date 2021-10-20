import asyncio
import ipaddress


from utils.connection.nosql.db import client
from utils.cache import gg_cache
from models.helper import IP

from fastapi import Request, HTTPException
from fastapi.logger import logger

from main import gg

@gg.middleware("http")
async def mw_check_ip(request: Request, call_next):
    client_ip = IP(request.client.host)
    # print("client access with ip: %s" % client_ip)
    if await check_ip(client_ip):
        raise HTTPException(403, "Your are not allowed to access this server.")
    response = await call_next(request)
    return response


@gg_cache
def _check_db(ip: int, version: int):
    if version == 4:
        ret = client.ip_blacklist.find_one({
            "lower": { "$lte" : ip },
            "higher": { "$gte": ip },
            "version": 4
        })
        return ret is not None
    else:
        higher64 = ip >> 64
        lower64 = ip & 0xffffffffffffffffffff
        ret = client.ip_blacklist.find_one({
            "lower": { "$lte" : higher64 },
            "higher": { "$gte": higher64 },
            "sub_higher": {"$gte": lower64},
            "sub_lower": {"$lte": lower64},
            "version": 6,
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
        ipv6 = int(ipaddress.ip_address(ip.ipv6))
        ret = ret or _check_db(ipv6, 6)
    return ret