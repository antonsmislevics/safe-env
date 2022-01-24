from . import BaseValue
from typing import Dict
from ..templatedconfigurationmixin import TemplatedConfigurationMixin


class BaseValueWithTemplatedConfiguration(TemplatedConfigurationMixin, BaseValue):
    def __init__(self, type_name: str, name: str, templated_args: Dict[str, str], templated_args_value_providers: Dict):
        super().__init__(templated_args=templated_args,
                         templated_args_value_providers=templated_args_value_providers,
                         type_name=type_name,
                         name=name)


    def get_value(self, raw: bool = False):
        self.ensure_templated_config_loaded()
        return super().get_value(raw)
