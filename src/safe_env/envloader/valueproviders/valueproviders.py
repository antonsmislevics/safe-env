import os
from typing import Dict, List
from . import BaseValueProvider
from ..values import TemplatedValue


class DictValueProvder(BaseValueProvider):
    def __init__(self, values: Dict[str, str], **kwargs):        
        super().__init__(**kwargs)
        self.values = values

    def is_known_value(self, name) -> bool:
        return True


class HostEnvValueProvider(DictValueProvder):
    def __init__(self, **kwargs):
        super().__init__(os.environ, **kwargs)
        self.aliases = ["ENV"]


class TemplatedValueProvider(BaseValueProvider):
    def __init__(self, aliases: List[str], templated_value_dict: Dict[str, str], value_providers: Dict, **kwargs):
        super().__init__(**kwargs)
        self.aliases = aliases
        default_alias = self.default_alias
        for key, value in templated_value_dict.items():
            self.values[key] = TemplatedValue(default_alias, key, value, value_providers)
        

class ParamValueProvider(TemplatedValueProvider):
    def __init__(self, **kwargs):
        super().__init__(aliases=["PARAM"], **kwargs)
