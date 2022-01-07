from typing import List, Dict
from . import BaseValue, TemplatedValue
from ..vaults import BaseVault
from ...models import SecretConfig


class SecretValue(BaseValue):
    def __init__(self, name: str, vault_name: str, name_in_vault: str, service_name_in_keyring: str, name_in_keyring: str, is_local_only: bool, keyring: BaseVault, vaults: List[BaseVault], force_reload_from_remote: bool = False):
        type_name = "SECRET"
        super().__init__(type_name, name)
        self.vault_name = vault_name
        if not(name_in_vault):
            name_in_vault = name
        self.name_in_vault = name_in_vault
        if not(name_in_keyring):
            name_in_keyring = name
        self.name_in_keyring = name_in_keyring
        self.is_local_only = is_local_only
        self.is_resource_cache = False
        self.keyring = keyring
        self.service_name_in_keyring = service_name_in_keyring
        self.vaults = vaults
        self.force_reload_from_remote = force_reload_from_remote
        self.id = None
    
    def get_service_name(self):
        service_name = self.service_name_in_keyring
        if not(service_name):
            if self.keyring:
                service_name = self.keyring.default_service_name
        return service_name
            
    def _get_vault_by_name(self, name) -> BaseVault:
        vault = next((x for x in self.vaults if x.name == name), None)
        if not(vault):
            raise Exception(f"Vault '{name}' cannot be found.")
        return vault
    
    def _get_value_from_vault(self, vault: BaseVault):
        value = None
        secret = vault.get(self.name_in_vault)
        if secret:
            # value is found in vault - save the value locally
            value = secret.value
            self.id = secret.id
            if self.keyring:
                self.keyring.set(self.name_in_keyring, value, self.service_name_in_keyring)
        return value

    def _get_value(self):
        value = None

        is_local = self.is_local_only or self.is_resource_cache
        
        if self.keyring and (is_local or not(self.force_reload_from_remote)):
            # 1. check local keyring
            value = self.keyring.get(self.name_in_keyring, self.service_name_in_keyring)

        if not(value) and not(is_local):
            # 2. value is not found locally -> check remote vaults
            if self.vault_name:
                # default vault name is specified - check default vault
                vault = self._get_vault_by_name(self.vault_name)
                value = self._get_value_from_vault(vault)
            else:
                for vault in self.vaults:
                    value = self._get_value_from_vault(vault)
                    if value:
                        # value is already found - do not check other vaults
                        break
        return value

    @staticmethod    
    def load_from_config(settings: SecretConfig, value_providers: Dict, keyring: BaseVault, vaults: List[BaseVault], force_reload_from_remote: bool = False):
        name = settings.name
        is_local_only = settings.local

        vault = TemplatedValue(None,
                                    "vault",
                                    settings.vault,
                                    value_providers).get_value()
        vault_name = TemplatedValue(None,
                                    "vault_name",
                                    settings.vault_name,
                                    value_providers).get_value()
        keyring_service_name = TemplatedValue(None,
                                    "keyring_service_name",
                                    settings.keyring_service_name,
                                    value_providers).get_value()
        keyring_name = TemplatedValue(None,
                                    "keyring_name",
                                    settings.keyring_name,
                                    value_providers).get_value()
        return SecretValue(name, vault, vault_name, keyring_service_name, keyring_name, is_local_only, keyring, vaults, force_reload_from_remote)
