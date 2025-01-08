from typing import Any
from .base_cache_provider import BaseCacheProvider

class MemoryCache(BaseCacheProvider):
    _cache_dict = dict()

    def __init__(self):
        super().__init__(as_json=False)
    
    def _get(self, name: str):
        return __class__._cache_dict.get(name)

    def _set(self, name: str, value: Any):
        __class__._cache_dict[name] = value
    
    def _delete(self, name: str):
        pass

