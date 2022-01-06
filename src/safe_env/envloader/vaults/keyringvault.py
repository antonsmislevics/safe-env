import keyring
from typing import Dict
from ...models import LocalKeyringSettings
from . import BaseVault
from ..values import TemplatedValue


class KeyringVault(BaseVault):
    def __init__(self, keyring_type: str = None, service_name: str = None, is_ready: bool = True):
        super().__init__(name="LocalKeyring")

        if service_name is None:
            is_ready = False

        self.keyring_type = keyring_type
        self.default_service_name = service_name
        self.is_ready = is_ready
        
        self.init_keyring()

    def init_keyring(self):
        if not(self.is_ready):
            return
        # TODO: Currently is using default OS keyring.
        #       Implement custom keyrings with keyring.set_keyring() with correct keyring type.
        pass

    def load_from_settings(self, settings: LocalKeyringSettings, value_providers: Dict):
        self.is_ready = False
        keyring_type = TemplatedValue(None,
                                      "keyring_type",
                                      settings.type,
                                      value_providers).get_value()
        service_name = TemplatedValue(None,
                                      "service_name",
                                      settings.service_name,
                                      value_providers).get_value()
        self.keyring_type = keyring_type
        self.default_service_name = service_name
        self.is_ready = True
        self.init_keyring()

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
