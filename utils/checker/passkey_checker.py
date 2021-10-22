import asyncio
import ipaddress

from functools import lru_cache

from utils.connection.nosql.db import client
from models.user.user import get_userid_by_passkey

from fastapi.logger import logger

def check_passkey(passkey: str):
    """
        Check if a passkey is exsit.

        _ret_: Coroutine object. To get result, use `await` keyword.

            a userid will be returned
    """
    return asyncio.create_task(_check_passkey(passkey))

async def _check_passkey(passkey: str):
    return get_userid_by_passkey(passkey)
