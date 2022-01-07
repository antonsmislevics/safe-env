from abc import abstractmethod
from typing import Dict, Any

class BaseResourceHandler():
    def __init__(self, name: str):
        self.name = name
    
    def load_resource(self) -> Dict[str, Any]:
        # TODO: add common logging
        return self._load_resource()

    @abstractmethod
    def _load_resource(self) -> Dict[str, Any]:
        pass
