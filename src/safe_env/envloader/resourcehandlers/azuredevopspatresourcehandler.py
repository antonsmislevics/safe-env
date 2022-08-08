from abc import abstractmethod
from typing import Dict, Any
from .baseresourcehandlerwithtemplatedconfiguration import BaseResourceHandlerWithTemplatedConfiguration
from urllib.parse import urlparse, urlunparse
import keyring


class AzureDevOpsPATResourceHandler(BaseResourceHandlerWithTemplatedConfiguration):
    def __init__(self, name: str, query: str = None, index_url: str = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None):
        super().__init__(name, query, templated_args, templated_args_value_providers)
        self.index_url = index_url


    def on_templated_config_loaded(self):
        pass


    def _load_resource(self) -> Dict[str, Any]:
        creds = keyring.get_credential(self.index_url, None)
        if creds is None:
            raise Exception(f"Cannot retrieve Azure DevOps PAT for {self.index_url}")
        
        parsed_index_url = urlparse(self.index_url)

        username = parsed_index_url.username or 'azure'
        password = creds.password
        hostname = parsed_index_url.hostname

        parsed_index_url_with_creds = parsed_index_url._replace(netloc=f"{username}:{password}@{hostname}")
        
        return {
            'username': creds.username,
            'password': creds.password,
            'url': urlunparse(parsed_index_url_with_creds)
        }

