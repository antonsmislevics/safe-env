from abc import abstractmethod
from typing import Dict, Any
import jmespath

class BaseResourceHandler():
    def __init__(self, name: str, query: str = None):
        self.name = name
        self.query = query


    def load_resource(self) -> Dict[str, Any]:
        obj = self._load_resource()
        if self.query:
            value = jmespath.search(self.query, obj)
        else:
            value = obj
        return value


    @abstractmethod
    def _load_resource(self) -> Dict[str, Any]:
        pass
