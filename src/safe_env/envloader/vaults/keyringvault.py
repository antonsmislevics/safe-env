from __future__ import annotations
import keyring
from typing import Dict
from .basevaultwithtemplatedconfiguration import BaseVaultWithTemplatedConfiguration
from ...models import LocalKeyringSettings


class KeyringVault(BaseVaultWithTemplatedConfiguration):
    def __init__(self, keyring_type: str = None, service_name: str = None, templated_args: Dict[str, str] = None, templated_args_value_providers: Dict = None):
        super().__init__(name="LocalKeyring", templated_args=templated_args, templated_args_value_providers=templated_args_value_providers)

        self.keyring_type = keyring_type
        self.default_service_name = service_name
        self.is_ready = False


    @staticmethod
    def load_from_config(settings: LocalKeyringSettings, value_providers: Dict) -> KeyringVault:
        templated_args = {
            "keyring_type": settings.type,
            "default_service_name": settings.service_name,
        }
        return KeyringVault(templated_args=templated_args, templated_args_value_providers=value_providers)


    def init_vault(self):
        # TODO: Currently is using default OS keyring.
        #       Implement custom keyrings with keyring.set_keyring() with correct keyring type.
        
        # call BaseVault to finalize initialization
        super().init_vault()


    def _get(self, name: str, service_name: str=None) -> str:
        if not(service_name):
            service_name = self.default_service_name
        value = keyring.get_password(service_name, name)
        return value


    def _set(self, name: str, value: str, service_name: str=None):
        if not(service_name):
            service_name = self.default_service_name
        keyring.set_password(service_name, name, value)


    def _delete(self, name: str, service_name: str=None):
        if not(service_name):
            service_name = self.default_service_name
        keyring.delete_password(service_name, name)
