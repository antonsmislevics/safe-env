from typing import List, Dict

from typing import Dict, Callable
from ...models import ResourceConfig
from . import BaseValueProvider
from ..values.resourcevalue import ResourceValue
from ..values.secretvalue import SecretValue

class ResourceValueProvider(BaseValueProvider):
    def __init__(self, resources: List[ResourceConfig],
                       secret_values: Dict[str, SecretValue],
                       get_resource_template_delegate: Callable,
                       value_providers: Dict,
                       force_reload_from_remote: bool = False,
                       do_not_cache: bool = False, **kwargs):
        super().__init__(**kwargs)
        default_alias = "RESOURCE"
        self.aliases = [default_alias]

        for resource_config in resources:
            resource = ResourceValue.load_from_config(resource_config, secret_values, self.values, get_resource_template_delegate, value_providers, force_reload_from_remote, do_not_cache)
            self.values[resource.name] = resource
