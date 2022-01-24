from __future__ import annotations
from typing import Dict, Any
from .basevaultwithtemplatedconfiguration import BaseVaultWithTemplatedConfiguration
from . import AzureKeyVault
from ... import utils
from ...models import VaultConfig


class DelayedLoadVault(BaseVaultWithTemplatedConfiguration):
    def __init__(self, name: str, vault_type: str = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None, vault_templated_args: Dict[str, str] = None):
        super().__init__(name=name, templated_args=templated_args, templated_args_value_providers=templated_args_value_providers)

        self.vault_type = vault_type
        self.vault_templated_args = vault_templated_args
        self.templated_args_value_providers = templated_args_value_providers
        self.vault = None   # type: BaseVaultWithTemplatedConfiguration


    @staticmethod
    def load_from_config(settings: VaultConfig, value_providers: Dict) -> DelayedLoadVault:
        name = settings.name
        templated_args = {
            "vault_type": settings.type
        }
        vault_templated_args = settings.params
        return DelayedLoadVault(name=name,
                                templated_args=templated_args,
                                templated_args_value_providers=value_providers,
                                vault_templated_args=vault_templated_args)


    def init_vault(self):
        expected_types = [AzureKeyVault]
        vault_class = utils.type_name_to_type(self.vault_type, expected_types)
        self.vault = vault_class(name=self.name, templated_args=self.vault_templated_args, templated_args_value_providers=self.templated_args_value_providers)
        super().init_vault()


    def _get(self, name: str, service_name: str=None) -> str:
        return self.vault.get(name, service_name)

    def _set(self, name: str, value: str, service_name: str=None):
        return self.vault.set(name, value, service_name)

    def _delete(self, name: str, service_name: str=None):
        return self.vault.delete(name, service_name)
