from fastapi.logger import logger
from fastapi import Request
import re

from utils.connection.nosql.db import client, _client
from utils.cache import gg_cache
from models.torrent_client import TorrentClient
from models.helper import ErrorException

browser_regex = re.compile('(Mozilla|Browser|WebKit|Opera|Links|Lynx|[Bb]ot)')
torrent_clients = [TorrentClient(**record) for record in _client.user_agent.find()]

@gg_cache(cache_type='py_lru_cache') #since the torrent_clients are all locally pre generated, we don't want to re-instantiate them back from redis
def _check_db(ua: str):
    for client in torrent_clients:
        if ua in client:
            return client
    raise ErrorException("No valid torrent client detected")

async def check_ua_or_400(request: Request):
    """
        Check if a given ua is a browser or cheat.

        _ret_: Coroutine object. To get result, use `await` keyword.

    """
    ua = request.headers.get('user-agent')

    # TODO: not tested yet
    peer_id = request._query_params.get('peer_id')
    key = request._query_params.get('key')
    if "want-digest" in request.headers or (key in peer_id): # check aria2
        raise ErrorException("You are not allowed to use this client.")

    logger.debug("Checking user agent: %s" % (ua))
    if browser_regex.match(ua):
        raise ErrorException("You are not allowed to access this with browser.")
    
    if "cookie" in request.headers or "accept-charset" in request.headers:
        ErrorException("Go away cheater!")
    client = _check_db(ua)
    return client