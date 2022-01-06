from typing import Any, Dict
from ...models import VaultConfig
# from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.keyvault.secrets import SecretClient
from . import BaseVault
from ..values import TemplatedValue


class AzureKeyVault(BaseVault):
    def __init__(self, name: str, url: str = None, credential: Any = None, is_ready: bool = True):
        super().__init__(name=name)

        if url is None:
            is_ready = False

        self.url = url
        self.credential = credential
        self.is_ready = is_ready
        self.client = None
        self.init_keyvault()

    def init_keyvault(self):
        if not(self.is_ready):
            return
        self.client = SecretClient(vault_url=self.url, credential=self.credential)

    def load_from_settings(self, settings: VaultConfig, value_providers: Dict):
        # TODO: add support for multiple types (move to separate class)
        #       currently only azure keyvault is supported

        self.is_ready = False
        name = settings.name
        vault_type = TemplatedValue(None,
                                      "vault_type",
                                      settings.type,
                                      value_providers).get_value()
        vault_url = TemplatedValue(None,
                                      "vault_url",
                                      settings.params['url'],
                                      value_providers).get_value()
        vault_credential_name = TemplatedValue(None,
                                      "vault_credential",
                                      settings.params['credential'],
                                      value_providers).get_value()
        credential_name_to_type_mapping = {
            "DefaultAzureCredential": DefaultAzureCredential,
            "AzureCliCredential": AzureCliCredential
        }
        if vault_credential_name:
            vault_credential_type = credential_name_to_type_mapping.get(vault_credential_name)
            if not(vault_credential_type):
                raise Exception(f"Unknown vault credential type: {vault_credential_name}")
        else:
            vault_credential_type = DefaultAzureCredential

        self.name = name
        self.url = vault_url
        self.credential = vault_credential_type()
        self.is_ready = True
        self.init_keyvault()

    def _get(self, name: str, service_name: str=None) -> str:
        value = self.client.get_secret(name)
        return value

    def _set(self, name: str, value: str, service_name: str=None):
        self.client.set_secret(name, value)

    def _delete(self, name: str, service_name: str=None):
        self.client.begin_delete_secret(name)
