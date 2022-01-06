from abc import abstractmethod
from enum import Enum


class ValueStatus(Enum):
    NotLoaded = 0
    Processing = 1
    Loaded = 2


class BaseValue():
    def __init__(self, type_name: str, name: str):
        self.type_name = type_name
        self.name = name
        self.value = None
        self.status = ValueStatus.NotLoaded


    def get_value(self):
        if self.status == ValueStatus.Processing:
            raise Exception(f"Circuluar dependency found while loading {self.type_name}:{self.name}")

        if self.status == ValueStatus.Loaded:
            return self.value
        
        self.status = ValueStatus.Processing
        self.value = self._get_value()
        self.status = ValueStatus.Loaded
        return self.value


    @abstractmethod
    def _get_value(self):
        pass
