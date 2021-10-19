
import redis

from main import config


caches = []


client = redis.StrictRedis(**config.cache.redis)
from redis_lru import RedisLRU
redis_lru_cache = RedisLRU(client)
# from .redis_lru_cache import lru_cache_redis

def gg_cache(func=None, cache_type='lru_cache', maxsize=None):
    # print("GG Cache:", func.__name__, func.__module__)
    if cache_type == 'lru_cache':
        func_path = f"{func.__module__}.{func.__name__}"
        if maxsize is None:
            try:
                maxsize = eval(f"config.cache.{func_path}")
                print(f"Use maxsize from config for{func_path}:", maxsize)
            except:
                pass
        @redis_lru_cache
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        caches.append(wrapper)
        return wrapper
    if cache_type == 'timed_cache':
        def wrapper(func=None, *args, **kwargs):
            func_path = f"{func.__module__}.{func.__name__}"
            try:
                _config = eval(f"config.cache.{func_path}")
                print(f"Use config from config for{func_path}:", _config)
            except:
                pass
            @redis_lru_cache(ttl=_config.ttl)
            def _wrapped(*args, **kwargs):
                return func(*args, **kwargs)
            return _wrapped
        if func is not None:
            return wrapper(func)
        else:
            return wrapper


def clear_cache():
    redis_lru_cache.clear_all_cache()

