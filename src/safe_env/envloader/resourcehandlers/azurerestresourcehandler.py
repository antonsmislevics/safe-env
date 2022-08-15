from abc import abstractmethod
from typing import Dict, Any
from .baseresourcehandlerwithtemplatedconfiguration import BaseResourceHandlerWithTemplatedConfiguration
import requests
import urllib.parse
from ... import utils


class AzureRESTResourceHandler(BaseResourceHandlerWithTemplatedConfiguration):
    def __init__(self, name: str, query: str = None, url: str = None, method: str = None, credential: Any = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None):
        super().__init__(name, query, templated_args, templated_args_value_providers)
        self.credential = credential
        self.method = method
        self.url = url


    def on_templated_config_loaded(self):
        self.azure_management_scope = "https://management.core.windows.net/.default"
        self.azure_management_url = "https://management.azure.com"
        self.url = urllib.parse.urljoin(self.azure_management_url, self.url)
        
        if not(self.method) or not(self.method.upper() in ["GET", "POST"]):
            self.method = "GET"
        else:
            self.method = self.method.upper()
        
        if isinstance(self.credential, str):
            self.credential = utils.azure_credentials_name_to_type(self.credential)()


    def _load_resource(self) -> Dict[str, Any]:
        credential_token = self.credential.get_token(self.azure_management_scope)
        headers = {"Authorization": 'Bearer ' + credential_token.token}
        resp = requests.request(method=self.method, url=self.url, headers=headers)
        return resp.json()

