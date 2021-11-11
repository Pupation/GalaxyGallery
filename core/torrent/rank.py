from fastapi import Depends
import aioredis as redis
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.sql.functions import rank

from . import router
from utils.cache import redis_connection_pool, gg_cache
from models.user.auth import current_active_user
from models.user.user import User

def get_rank_name(date: datetime):
    return f"{get_rank_name.__module__}:{date.strftime('%Y%m%d')}"

async def query_keyword(keyword: str):
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    now = datetime.now()
    key_name = query_keyword.__module__ + ':' + now.strftime('%Y%m%d')
    await client.zincrby(key_name, 1, keyword)
    await client.expireat(key_name, now.replace(second=0, microsecond=0, minute=0, hour=0, day=now.day + 4))
    # print(await client.zscore(key_name, keyword))

async def get_trending_keyword(keyword: str):
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    key_name = get_trending_keyword.__module__+':trending'
    if await client.exists(key_name) == 0:
        dates = datetime.now()
        expire = dates.replace(second=0, microsecond=0, minute=0, hour= dates.hour + 1)
        rank_names = {}
        for i in range(3):
            rank_name = get_rank_name(dates)
            if await client.exists(rank_name) != 0:
                rank_names[rank_name] = 2 - 0.5 * i
            dates -= timedelta(days=1)
        if len(rank_names.keys()) == 0:
            return []
        await client.zunionstore(key_name, rank_names)
        await client.expireat(key_name, expire)
    ret = []
    if keyword == '':
        for keyword, val in await client.zrevrange(key_name, 0, 20, True):
            if val > 10:
                ret.append((keyword.decode('utf-8'), int(val)))
            else:
                break
        return ret
    else:
        return await search_suggestion(keyword)

@gg_cache(cache_type='timed_cache')
async def search_suggestion(keyword: str) -> List[tuple]:
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    key_name = get_trending_keyword.__module__+':trending'
    ret = []
    while True:
            cursor = 0
            cur, records = await client.zscan(key_name, cursor, match=f"*{keyword}*", count=100)
            cursor = cur
            for key, val in records:
                ret.append((key.decode('utf-8'), int(val)))
            if len(records) < 100:
                    break
    ret.sort(key=lambda x: x[1])
    return ret[:5]

@router.get('/trending')
async def search_trending(keyword:str = '', _: User = Depends(current_active_user)):
    return await get_trending_keyword(keyword)