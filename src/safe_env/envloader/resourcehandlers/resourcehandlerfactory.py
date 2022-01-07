from typing import Dict
from . import BaseResourceHandler, AzureRESTResourceHandler
from ..values import TemplatedValue
from ... import utils

class ResourceHandlerFactory:
    @staticmethod
    def create(name: str, type_name_template: str, params: Dict[str, str], value_providers: Dict) -> BaseResourceHandler:
        resource_type_name = TemplatedValue(None,
                                    "type",
                                    type_name_template,
                                    value_providers).get_value()
        processed_params = {}
        for key, value in params.items():
            processed_params[key] = TemplatedValue(None,
                                    f"param_{key}",
                                    value,
                                    value_providers).get_value()
        
        credential_type = utils.azure_credentials_name_to_type(processed_params.get("credential"))
        processed_params["credential"] = credential_type()

        expected_types = [AzureRESTResourceHandler]
        resource_type = utils.type_name_to_type(f"{resource_type_name}ResourceHandler", expected_types)
        return resource_type(name=name, **processed_params)
