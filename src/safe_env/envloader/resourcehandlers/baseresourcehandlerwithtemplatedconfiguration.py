from abc import abstractmethod
from typing import Dict, Any
from . import BaseResourceHandler
from ..templatedconfigurationmixin import TemplatedConfigurationMixin


class BaseResourceHandlerWithTemplatedConfiguration(TemplatedConfigurationMixin, BaseResourceHandler):
    def __init__(self, name: str, query: str = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None):
        super().__init__(templated_args, templated_args_value_providers, name, query)
    
    def load_resource(self) -> Dict[str, Any]:
        self.ensure_templated_config_loaded()
        return super().load_resource()

