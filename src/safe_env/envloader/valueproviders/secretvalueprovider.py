from typing import List, Dict
from . import BaseValueProvider
from ...models import SecretConfig
from ..vaults import BaseVault
from ..values import SecretValue


class SecretValueProvider(BaseValueProvider):
    def __init__(self, secrets: List[SecretConfig], value_providers: Dict, keyring: BaseVault, vaults: List[BaseVault], force_reload_from_remote: bool = False, **kwargs):
        super().__init__(**kwargs)
        default_alias = "SECRET"
        self.aliases = [default_alias]
        self.keyring = keyring
        self.vaults = vaults
        self.force_reload_from_remote = force_reload_from_remote

        for secret_config in secrets:
            secret = SecretValue.load_from_config(secret_config, value_providers, keyring, vaults, force_reload_from_remote)
            self.values[secret.name] = secret

    def add_value(self, name):
        secret = SecretValue(name, None, None, None, None, False, self.keyring, self.vaults, self.force_reload_from_remote)
        self.values[secret.name] = secret

