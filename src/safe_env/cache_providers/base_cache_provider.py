from abc import abstractmethod
from typing import Any
import json


class BaseCacheProvider():
    def __init__(self, as_json: bool = True):
        self.store_as_json = as_json
        
    @abstractmethod
    def _get(self, name: str, *args, **kwargs) -> Any:
        pass

    def get(self, name: str, *args, **kwargs) -> Any:
        value = self._get(name, *args, **kwargs)
        if self.store_as_json:
            if value is not None:
                value = json.loads(value)
        return value

    @abstractmethod
    def _set(self, name: str, value: Any, *args, **kwargs):
        pass

    def set(self, name: str, value: Any, *args, **kwargs):
        if self.store_as_json:
            if value is not None:
                value = json.dumps(value)
        self._set(name, value, *args, **kwargs)
    
    @abstractmethod
    def _delete(self, name: str, *args, **kwargs):
        pass

    def delete(self, name: str, *args, **kwargs):
        self._delete(name, *args, **kwargs)
