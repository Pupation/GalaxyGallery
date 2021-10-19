
from functools import lru_cache

from main import config

from .timed_cache import timed_lru_cache

caches = []

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
        @lru_cache(maxsize=maxsize)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        caches.append(wrapper)
        return wrapper
    if cache_type == 'timed_cache':
       return timed_lru_cache


def clear_cache():
    for cache in caches:
        cache.cache_clear()

