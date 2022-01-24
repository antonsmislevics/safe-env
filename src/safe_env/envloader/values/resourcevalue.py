from __future__ import annotations
from typing import List, Dict, Any, Callable, Union
import jmespath

from . import SecretValue
from .basevaluewithtemplatedconfiguration import BaseValueWithTemplatedConfiguration
from ..resourcehandlers import BaseResourceHandler
from ..resourcehandlers.delayedloadresourcehandler import DelayedLoadResourceHandler
from ...models import ResourceConfig


class ResourceValue(BaseValueWithTemplatedConfiguration):
    def __init__(self,
                 name: str,
                 handler: Union[BaseResourceHandler, str] = None,
                 handler_params: Dict[str, str] = None,
                 cache_secret: Union[SecretValue, str] = None,
                 parent: Union[ResourceValue, str] = None,
                 query: str = None,
                 secret_values: Dict[str, SecretValue] = None,
                 resource_values: Dict[str, ResourceValue] = None,
                 get_resource_template_delegate: Callable = None,
                 templated_args: Dict[str,str] = None,
                 templated_args_value_providers: Dict = None,
                 force_reload_from_remote: bool = False,
                 do_not_cache: bool = False):
        type_name = "RESOURCE"
        super().__init__(type_name=type_name, 
                         name=name,
                         templated_args=templated_args,
                         templated_args_value_providers=templated_args_value_providers)
        self.resource_values = resource_values
        self.secret_values = secret_values
        self.get_resource_template_delegate = get_resource_template_delegate
        self.value_providers = templated_args_value_providers
        self.handler = handler
        self.handler_params = handler_params
        self.query = query
        self.parent = parent
        self.cache_secret = cache_secret
        
        self.force_reload_from_remote = force_reload_from_remote
        self.do_not_cache=do_not_cache

    def on_templated_config_loaded(self):
        if self.parent and isinstance(self.parent, str):
            parent_resource = self.resource_values.get(self.parent)
            if parent_resource:
                self.parent = parent_resource
            else:
                raise Exception(f"Cannot load resource '{self.name}' from configuraton: specified parent resource '{self.parent}' does not exist")

        if self.handler and isinstance(self.handler, str):
            handler_config = self.get_resource_template_delegate(self.handler)
            if handler_config:
                self.handler = DelayedLoadResourceHandler.load_from_config(handler_config, self.handler_params, self.value_providers)
            else:
                raise Exception(f"Cannot load resource '{self.name}' from configuraton: specified resource handler template '{self.handler}' does not exist")

        if self.cache_secret and isinstance(self.cache_secret, str):
            cache_secret_value = self.secret_values.get(self.cache_secret)
            if cache_secret_value:
                self.cache_secret = cache_secret_value
            else:
                raise Exception(f"Cannot load resource '{self.name}' from configuraton: specified cache secret '{self.cache_secret}' does not exist")

        super().on_templated_config_loaded()

    def _get_value(self):
        value = None
        cache_secret = self.cache_secret
        if cache_secret and not(self.force_reload_from_remote):
            # 1. check if cached value exists
            value = cache_secret.get_value()

        if not(value):
            if self.parent:
                # 2. load value from parent
                if self.query:
                    parent_value = self.parent.get_value(raw=True)
                    if parent_value:
                        value = jmespath.search(self.query, parent_value)
                else:
                    value = self.parent.get_value()
            elif self.handler:
                # 3. download value using resource handler
                obj = self.handler.load_resource()
                if obj:
                    if self.query:
                        value = jmespath.search(self.query, obj)
                    else:
                        value = obj

            if cache_secret and not(self.do_not_cache):
                cache_secret.update_value(value)

        return value

    @staticmethod
    def load_from_config(settings: ResourceConfig,
                         secret_values: Dict[str, SecretValue],
                         resource_values: Dict[str, ResourceValue],
                         get_resource_template_delegate: Callable,
                         value_providers: Dict,
                         force_reload_from_remote: bool = False,
                         do_not_cache: bool = False) -> ResourceValue:
        name = settings.name
                
        templated_args = {
            "query": settings.query,
            "parent": settings.parent,
            "handler": settings.template,
            "cache_secret": settings.cache_secret
        }
        
        return ResourceValue(name,
                             handler_params=settings.params,
                             secret_values=secret_values,
                             resource_values=resource_values,
                             get_resource_template_delegate=get_resource_template_delegate,
                             templated_args=templated_args,
                             templated_args_value_providers=value_providers,
                             force_reload_from_remote=force_reload_from_remote,
                             do_not_cache=do_not_cache)
