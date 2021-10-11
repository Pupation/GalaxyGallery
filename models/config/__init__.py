from typing import Any
from yaml import safe_load
from dotmap import DotMap

class Config(dict):
    def __init__(self, path):
        self.config = DotMap(safe_load(open(path, 'r')))

    def __getattr__(self, key: str) -> DotMap:
        return self.config.get(key)