from typing import Any, Dict
from ...models import VaultConfig
# from azure.core.credentials import TokenCredential
from azure.keyvault.secrets import SecretClient
from . import BaseVault
from ..values import TemplatedValue
from ... import utils
from .basevaultwithtemplatedconfiguration import BaseVaultWithTemplatedConfiguration


class AzureKeyVault(BaseVaultWithTemplatedConfiguration):
    def __init__(self, name: str, url: str = None, credential: Any = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None):
        super().__init__(name=name, templated_args=templated_args, templated_args_value_providers=templated_args_value_providers)

        self.url = url
        self.credential = credential
        self.is_ready = False
        self.client = None


    def init_vault(self):
        if isinstance(self.credential, str):
            self.credential = utils.azure_credentials_name_to_type(self.credential)()

        self.client = SecretClient(vault_url=self.url, credential=self.credential)
        super().init_vault()


    def _get(self, name: str, service_name: str=None) -> str:
        value = None
        try:
            value = self.client.get_secret(name)
        except ValueError:
            # secret with this name was not found in keyvault
            pass
        return value

    def _set(self, name: str, value: str, service_name: str=None):
        self.client.set_secret(name, value)

    def _delete(self, name: str, service_name: str=None):
        # NOTE: deleting for keyvault is not performed because it is not clear how soft delete will work with caching for resources
        pass
        # self.client.begin_delete_secret(name)
        # self.client.purge_deleted_secret(name)
