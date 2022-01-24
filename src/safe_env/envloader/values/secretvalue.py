from __future__ import annotations
from typing import List, Dict
from .basevaluewithtemplatedconfiguration import BaseValueWithTemplatedConfiguration
from ..vaults import BaseVault
from ...models import SecretConfig


class SecretValue(BaseValueWithTemplatedConfiguration):
    def __init__(self,
                 name: str,
                 vault_name: str = None,
                 name_in_vault: str = None,
                 service_name_in_keyring: str = None,
                 name_in_keyring: str = None,
                 is_local_only: bool = None,
                 keyring: BaseVault = None,
                 vaults: List[BaseVault] = None,
                 templated_args: Dict[str,str] = None,
                 templated_args_value_providers: Dict = None,
                 force_reload_from_remote: bool = False,
                 do_not_cache: bool = False):
        type_name = "SECRET"
        super().__init__(type_name=type_name,
                         name=name,
                         templated_args=templated_args,
                         templated_args_value_providers=templated_args_value_providers)
        self.vault_name = vault_name
        self.name_in_vault = name_in_vault
        self.name_in_keyring = name_in_keyring
        self.is_local_only = is_local_only
        self.keyring = keyring
        self.service_name_in_keyring = service_name_in_keyring
        self.vaults = vaults
        self.force_reload_from_remote = force_reload_from_remote
        self.do_not_cache = do_not_cache
        self.id = None


    def on_templated_config_loaded(self):
        if not(self.name_in_vault):
            self.name_in_vault = self.name
        if not(self.name_in_keyring):
            self.name_in_keyring = self.name
        super().on_templated_config_loaded()
    
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
            if not(self.do_not_cache):
                self.update_value(value, save_to_local_only=True)
        return value

    def _get_value(self):
        value = None

        is_local = self.is_local_only
        
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

    def _get_default_vault(self) -> BaseVault:
        vault = None
        if self.vault_name:
            vault = self._get_vault_by_name(self.vault_name)
        elif len(self.vaults) == 1:
            vault = self.vaults[0]
        else:
            raise Exception(f"Cannot determine default vault for secret '{self.name}': configuration file has multiple vaults, but vault for this secret is not specified.")
        return vault

    def update_value(self, value, save_to_local_only: bool = False):
        self.ensure_templated_config_loaded()
        # 1. save/delete value to/from local keyring
        if self.keyring:
            if not(self.do_not_cache) or self.is_local_only:
                # if do_not_cache is True, update only if secret is local
                if value:
                    self.keyring.set(self.name_in_keyring, value, self.service_name_in_keyring)
                else:
                    self.keyring.delete(self.name_in_keyring, self.service_name_in_keyring)
            
        # 2. save/delete value to/from vault
        if not(self.is_local_only) and not(save_to_local_only):
            vault = self._get_default_vault()
            if value:
                vault.set(self.name_in_vault, value)
            else:
                vault.delete(self.name_in_vault)

    @staticmethod
    def load_from_config(settings: SecretConfig, value_providers: Dict, keyring: BaseVault, vaults: List[BaseVault], force_reload_from_remote: bool = False, do_not_cache: bool = False) -> SecretValue:
        name = settings.name
        is_local_only = settings.local
        templated_args = {
            "vault_name": settings.vault,
            "name_in_vault": settings.vault_name,
            "service_name_in_keyring": settings.keyring_service_name,
            "name_in_keyring": settings.keyring_name
        }
        return SecretValue(name,
                           templated_args=templated_args,
                           templated_args_value_providers=value_providers,
                           is_local_only=is_local_only,
                           keyring=keyring,
                           vaults=vaults,
                           force_reload_from_remote=force_reload_from_remote,
                           do_not_cache=do_not_cache)
