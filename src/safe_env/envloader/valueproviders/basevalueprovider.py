from typing import List, Dict, Union
from ..values import BaseValue


class BaseValueProvider():
    def __init__(self, error_on_missing_value: bool=False):
        self._aliases = []
        self.error_on_missing_value = error_on_missing_value
        self._values = {} # type: Dict[str, Union[BaseValue, str]]

    @property
    def aliases(self) -> List[str]:
        return self._aliases
    
    @aliases.setter
    def aliases(self, value):
        self._aliases = value

    @property
    def default_alias(self) -> str:
        return self._aliases[0] if self._aliases else None

    @property
    def values(self) -> Dict[str, Union[BaseValue, str]]:
        return self._values

    @values.setter
    def values(self, value):
        self._values = value

    def is_known_value(self, name) -> bool:
        if name in self.values.keys():
            return True
        else:
            return False

    def add_value(self, name):
        pass

    def get_value(self, name) -> str:
        if name:
            name = name.strip()
        if not(self.is_known_value(name)):
            self.add_value(name)
        value = self.values.get(name)
        if isinstance(value, BaseValue):
            return value.get_value()
        else:
            return value

    def __format__(self, spec):
        value = self.get_value(spec)
        if self.error_on_missing_value and value is None:
            raise Exception(f"Cannot read value for '{self.default_alias}:{spec}'")
        return value or ""
