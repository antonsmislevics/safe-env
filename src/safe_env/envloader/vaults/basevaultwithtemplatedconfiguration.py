from abc import abstractmethod
from typing import Dict, Any
from . import BaseVault
from ..values import TemplatedValue
from ..templatedconfigurationmixin import TemplatedConfigurationMixin


class BaseVaultWithTemplatedConfiguration(TemplatedConfigurationMixin, BaseVault):
    def __init__(self, name: str, templated_args: Dict[str, str], templated_args_value_providers: Dict):
        super().__init__(templated_args, templated_args_value_providers, name)


    def on_templated_config_loaded(self):
        self.init_vault()


    def get(self, name: str, service_name: str=None) -> str:
        self.ensure_templated_config_loaded()
        return super().get(name, service_name)


    def set(self, name: str, value: str, service_name: str=None) -> str:
        self.ensure_templated_config_loaded()
        return super().set(name, value, service_name)


    def delete(self, name: str, service_name: str=None) -> str:
        self.ensure_templated_config_loaded()
        return super().delete(name, service_name)
