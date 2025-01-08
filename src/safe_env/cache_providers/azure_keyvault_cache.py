from azure.keyvault.secrets import SecretClient
from typing import Any
import logging
from .base_cache_provider import BaseCacheProvider

class AzureKeyVaultSecretCache(BaseCacheProvider):
    def __init__(self, url: str = None, credential: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.credential = credential
        self.client = SecretClient(vault_url=self.url, credential=self.credential)
    
    def _get(self, name: str) -> str:
        value = None
        try:
            secret = self.client.get_secret(name)
            if secret is not None:
                value = secret.value
        except ValueError:
            # secret with this name was not found in keyvault
            logging.error(f"Secret with specified name was not found in Azure KeyVault: {name}")
            # pass
        return value

    def _set(self, name: str, value: str):
        self.client.set_secret(name, value)

    def _delete(self, name: str):
        # NOTE: deleting for keyvault is not performed because it is not clear how soft delete will work with caching for resources
        logging.error("Deleting is not yet supported from Azure KeyVault.")
        # self.client.begin_delete_secret(name)
        # self.client.purge_deleted_secret(name)
