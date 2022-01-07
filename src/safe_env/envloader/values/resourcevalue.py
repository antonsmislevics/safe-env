from typing import List, Dict, Any
import jmespath
from . import BaseValue, SecretValue, TemplatedValue
from ..resourcehandlers import BaseResourceHandler, ResourceHandlerFactory
from ...models import ResourceConfig
# from ..valueproviders import BaseValueProvider


class ResourceValue(BaseValue):
    def __init__(self, name: str, handler: BaseResourceHandler, query: str, cache_secret: SecretValue, force_reload_from_remote: bool = False):
        type_name = "RESOURCE"
        super().__init__(type_name, name)
        self.handler = handler
        self.query = query
        self.cache_secret = cache_secret
        if self.cache_secret:
            self.cache_secret.is_resource_cache = True
        self.force_reload_from_remote = force_reload_from_remote


    def _get_value(self):
        value = None
        cache_secret = self.cache_secret
        if cache_secret and not(self.force_reload_from_remote):
            # 1. check if cached value exists
            value = cache_secret.get_value()

        if not(value):
            # 2. download value using resource handler
            obj = self.handler.load_resource()
            value = jmespath.search(self.query, obj)
             
            if cache_secret and cache_secret.keyring:
                # 3. update cached value
                if value:
                    cache_secret.keyring.set(cache_secret.name_in_keyring, value, cache_secret.service_name_in_keyring)
                else:
                    cache_secret.keyring.delete(cache_secret.name_in_keyring, cache_secret.service_name_in_keyring)

        return value

    @staticmethod    
    def load_from_config(settings: ResourceConfig, secret_values: Dict[str, SecretValue], value_providers: Dict, force_reload_from_remote: bool = False):
        name = settings.name
        cache_secret_name = settings.cache_secret

        cache_secret = None
        if cache_secret_name:
            cache_secret = secret_values.get(cache_secret_name)
            if not(cache_secret):
                raise Exception(f"Cannot load resource '{name}' from configuraton: specified cache secret '{cache_secret_name}' does not exist")

        query = TemplatedValue(None,
                                    "query",
                                    settings.query,
                                    value_providers).get_value()
        
        handler = ResourceHandlerFactory.create(name, settings.type, settings.params, value_providers)
        return ResourceValue(name, handler, query, cache_secret, force_reload_from_remote)
