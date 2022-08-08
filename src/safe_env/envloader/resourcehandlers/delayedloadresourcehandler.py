from __future__ import annotations
from typing import Dict, Any
from .baseresourcehandlerwithtemplatedconfiguration import BaseResourceHandlerWithTemplatedConfiguration
from ... import utils
from . import AzureRESTResourceHandler, AzureDevOpsPATResourceHandler
from ...models import ResourceTemplateConfig
from ..values import TemplatedValue
from ..valueproviders import DictValueProvder
from ..templatevalueproviders import TemplateValueProviders


class DelayedLoadResourceHandler(BaseResourceHandlerWithTemplatedConfiguration):
    def __init__(self, name: str,
                       resource_handler_type: str = None,
                       templated_args: Dict[str, str] = None,
                       templated_args_value_providers: Dict = None,
                       resource_handler_params: Dict[str, str] = None,
                       resource_handler_default_params: Dict[str, str] = None,
                       resource_handler_inputs: Dict[str, str] = None):
        super().__init__(name=name, templated_args=templated_args, templated_args_value_providers=templated_args_value_providers)

        self.resource_handler_type = resource_handler_type
        self.resource_handler_params = resource_handler_params
        self.resource_handler_default_params = resource_handler_default_params
        self.resource_handler_inputs = resource_handler_inputs
        self.templated_args_value_providers = templated_args_value_providers
        self.resource_handler = None   # type: BaseResourceHandlerWithTemplatedConfiguration


    @staticmethod
    def load_from_config(settings: ResourceTemplateConfig, params: Dict[str,str], value_providers: Dict) -> DelayedLoadResourceHandler:
        name = settings.name
        templated_args = {
            "resource_handler_type": settings.type
        }
        return DelayedLoadResourceHandler(name=name,
                                          templated_args=templated_args,
                                          templated_args_value_providers=value_providers,
                                          resource_handler_params=params,
                                          resource_handler_default_params = settings.params,
                                          resource_handler_inputs=settings.inputs)


    def on_templated_config_loaded(self):
        expected_types = [AzureRESTResourceHandler, AzureDevOpsPATResourceHandler]
        resource_handler_class = utils.type_name_to_type(f"{self.resource_handler_type}ResourceHandler", expected_types)

        processed_params = {}
        if self.resource_handler_params:
            for key, value in self.resource_handler_params.items():
                processed_params[key] = TemplatedValue(None,
                                                       f"resource_handler_param_{key}",
                                                       value,
                                                       self.templated_args_value_providers).get_value()

        if self.resource_handler_default_params:
            for key, value in self.resource_handler_default_params.items():
                if value:
                    current_value = processed_params.get(key)
                    if not(current_value):
                        processed_params[key] = value

        resource_handler_value_providers = TemplateValueProviders([
            DictValueProvder(["PARAM"], processed_params)
        ])

        resource_handler_templated_args = {}
        if self.resource_handler_inputs:
            resource_handler_templated_args = self.resource_handler_inputs.copy()

        self.resource_handler = resource_handler_class(name=self.name, templated_args=resource_handler_templated_args, templated_args_value_providers=resource_handler_value_providers)


    def _load_resource(self) -> Dict[str, Any]:
        return self.resource_handler.load_resource()
