from typing import Any
import keyring
from .base_cache_provider import BaseCacheProvider

class KeyringCache(BaseCacheProvider):
    def __init__(self, keyring_type: str = None, service_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.keyring_type = keyring_type
        self.default_service_name = service_name

        # TODO: Currently is using default OS keyring.
        #       Implement custom keyrings with keyring.set_keyring() with correct keyring type.

    def _get(self, name: str, service_name: str=None) -> Any:
        if not(service_name):
            service_name = self.default_service_name
        value = keyring.get_password(service_name, name)
        return value

    def _set(self, name: str, value: Any, service_name: str=None):
        if not(service_name):
            service_name = self.default_service_name
        keyring.set_password(service_name, name, value)

    def _delete(self, name: str, service_name: str=None):
        if not(service_name):
            service_name = self.default_service_name
        keyring.delete_password(service_name, name)
