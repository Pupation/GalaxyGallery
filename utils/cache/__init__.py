
import aioredis as redis

from main import config
from functools import lru_cache
from typing import Union, List


caches = []


redis_connection_pool = redis.ConnectionPool(**config.cache.redis)
client_lru = redis.StrictRedis(connection_pool=redis_connection_pool)
client_timed = redis.StrictRedis(connection_pool=redis_connection_pool)
from .aioredis import AioRedisLRU as RedisLRU
# redis_lru_cache = RedisLRU(client_lru, key_prefix='lru_cache')
# redis_timed_lru_cache = RedisLRU(client_timed, key_prefix='timed_lru_cache')

# from .redis_lru_cache import lru_cache_redis

def gg_cache(func=None, cache_type='lru_cache', maxsize=None):
    # print("GG Cache:", func.__name__, func.__module__)
    if cache_type == 'lru_cache':
        func_path = f"{func.__module__}.{func.__name__}"
        if maxsize is None:
            try:
                maxsize = eval(f"config.cache.{func_path}")
                print(f"[Redis Cache]Use maxsize from config for{func_path}:", maxsize)
            except:
                pass
        redis_lru_cache = RedisLRU(client_lru, key_prefix=func_path)
        @redis_lru_cache
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        caches.append(wrapper)
        return wrapper
    elif cache_type == 'timed_cache':
        def wrapper(func=None, *args, **kwargs):
            func_path = f"{func.__module__}.{func.__name__}"
            try:
                _config = eval(f"config.cache.{func_path}")
                print(f"Use config from config for{func_path}:", _config)
            except:
                pass
            redis_timed_lru_cache = RedisLRU(client_timed, key_prefix=func_path)
            @redis_timed_lru_cache(ttl=_config.ttl)
            def _wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return _wrapped
        if func is not None:
            return wrapper(func)
        else:
            return wrapper
    elif cache_type == 'py_lru_cache':
        def wrapper(func=None, *args, **kwargs):
            func_path = f"{func.__module__}.{func.__name__}"
            try:
                maxsize = eval(f"config.cache.{func_path}")
                print(f"[Py LRU Cache]Use maxsize from config for {func_path}:", maxsize)
            except:
                pass
            @lru_cache(maxsize=maxsize)
            def _wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return _wrapped
        
        return wrapper

def clear_cache():
    pass

def evict_cache_keyword(keyword: Union[str, List[str]]):
    client = redis.StrictRedis(connection_pool=redis_connection_pool)
    to_delete = []
    if not isinstance(keyword, list):
        keyword = [keyword]
    for key in keyword:
        to_delete += client.keys(f"*{key}*")
    if len(to_delete)> 0:
        client.delete(*to_delete)

