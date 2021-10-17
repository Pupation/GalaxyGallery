from functools import lru_cache
from fastapi.logger import logger
from fastapi import Request
import re

from utils.connection.nosql.db import client
from models.torrent_client import TorrentClient
from models.helper import ErrorException

browser_regex = re.compile('(Mozilla|Browser|WebKit|Opera|Links|Lynx|[Bb]ot)')
torrent_clients = [TorrentClient(**record) for record in client.user_agent.find()]

@lru_cache(maxsize = None)
def _check_db(ua: str):
    for client in torrent_clients:
        if ua in client:
            return client
    raise ErrorException("No valid torrent client detected")

def check_ua_or_400(request: Request):
    """
        Check if a given ua is a browser or cheat.

        _ret_: Coroutine object. To get result, use `await` keyword.

    """
    print(request.headers)
    ua = request.headers.get('user-agent')
    logger.debug("Checking user agent: %s" % (ua))
    if browser_regex.match(ua):
        raise ErrorException("You are not allowed to access this with browser.")
    
    if "cookie" in request.headers or "accept-charset" in request.headers:
        ErrorException("Go away cheater!")
    return _check_db(ua)