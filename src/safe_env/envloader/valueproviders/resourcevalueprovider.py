from typing import List, Dict

from safe_env.envloader.values.secretvalue import SecretValue
from ...models import ResourceConfig
from . import BaseValueProvider
from ..values import ResourceValue


class ResourceValueProvider(BaseValueProvider):
    def __init__(self, resources: List[ResourceConfig], secret_values: Dict[str, SecretValue], value_providers: Dict, force_reload_from_remote: bool = False, **kwargs):
        super().__init__(**kwargs)
        default_alias = "RESOURCE"
        self.aliases = [default_alias]
        self.force_reload_from_remote = force_reload_from_remote

        for resource_config in resources:
            resource = ResourceValue.load_from_config(resource_config, secret_values, value_providers, force_reload_from_remote)
            self.values[resource.name] = resource
