from typing import List, Dict
from . import BaseValueProvider
from ...models import SecretConfig
from ..vaults import BaseVault
from ..values import SecretValue


class SecretValueProvider(BaseValueProvider):
    def __init__(self, secrets: List[SecretConfig], value_providers: Dict, keyring: BaseVault, vaults: List[BaseVault], force_reload_from_remote: bool = False, do_not_cache: bool = False, **kwargs):
        super().__init__(**kwargs)
        default_alias = "SECRET"
        self.aliases = [default_alias]
        self.keyring = keyring
        self.vaults = vaults
        self.force_reload_from_remote = force_reload_from_remote
        self.do_not_cache = do_not_cache

        for secret_config in secrets:
            secret = SecretValue.load_from_config(secret_config, value_providers, keyring, vaults, force_reload_from_remote, do_not_cache)
            self.values[secret.name] = secret

    def add_value(self, name):
        secret = SecretValue(name, 
                             keyring = self.keyring,
                             vaults = self.vaults,
                             force_reload_from_remote = self.force_reload_from_remote,
                             do_not_cache=self.do_not_cache)
        self.values[secret.name] = secret

