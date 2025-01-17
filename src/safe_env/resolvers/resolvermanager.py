from omegaconf import OmegaConf

from .callables import KNOWN_CALLABLES
from .auth import KNOWN_AUTH_CLASSES
from .cache import KNOWN_CACHE_CLASSES


import logging
from operator import attrgetter
from importlib import import_module
from typing import Union, Callable, Tuple, Any, List
from collections import OrderedDict
from omegaconf.resolvers import oc
import jmespath
from ..models import (
    CallResolverParams,
    CacheProviderParams,
    ResolverConfiguration
)

from .delayedcallable import DelayedCallable

class ResolverManager():
    def __init__(self,
                 plugins_module_name,
                 plugins_module,
                 force_reload: bool=False,
                 no_cache: bool=False,
                 flush_caches: bool=False,
                 disable_unregistered_callables: bool = False,
                 load_known_callables_from_modules: List[str] = None):
        self.plugins_module_name = plugins_module_name
        self.plugins_module = plugins_module
        self.force_reload = force_reload
        self.no_cache = no_cache
        self.flush_caches = flush_caches
        self.disable_unregistered_callables = disable_unregistered_callables
        self.load_known_callables_from_modules = load_known_callables_from_modules

        self.builtin_resolvers = [
            ResolverConfiguration(
                name="se.call",
                func=self.call_by_type_name_resolver,
                use_cache=False
            ),
            ResolverConfiguration(
                name="se.delayed",
                func=self.call_delayed_resolver,
                use_cache=False
            ),
            ResolverConfiguration(
                name="se.cache",
                func=self.get_known_cache_class,
                use_cache=True
            ),
            ResolverConfiguration(
                name="se.auth",
                func=self.call_known_auth_class,
                use_cache=False
            )
        ]

        self.known_resolvers = []
        self.known_callables = dict()
        self.known_cache_classes = dict()
        self.known_auth_classes = dict()

    def _get_custom_modules_to_load_known_callables(self):
        custom_modules = []
        if self.plugins_module is not None:
            # plugins module is registered
            custom_modules.append(self.plugins_module)
        
        if self.load_known_callables_from_modules is not None:
            # names of additional modules were passed as parameter
            for module_name in self.load_known_callables_from_modules:
                custom_modules.append(self._get_module_by_name(module_name))
        return custom_modules

    def register_resolvers(self):
        self.known_resolvers = self.builtin_resolvers.copy()
        self.known_callables = KNOWN_CALLABLES.copy()
        self.known_cache_classes = KNOWN_CACHE_CLASSES.copy()
        self.known_auth_classes = KNOWN_AUTH_CLASSES.copy()

        custom_resolvers = []
        custom_modules = self._get_custom_modules_to_load_known_callables()
        for module in custom_modules:
            if hasattr(module, "CUSTOM_RESOLVERS"):
                custom_resolvers = getattr(module, "CUSTOM_RESOLVERS")
                self.known_resolvers += custom_resolvers

            if hasattr(module, "CUSTOM_CALLABLES"):
                custom_callables = getattr(module, "CUSTOM_CALLABLES")
                self.known_callables.update(custom_callables)
            
            if hasattr(module, "CUSTOM_CACHE_CLASSES"):
                custom_cache_classes = getattr(module, "CUSTOM_CACHE_CLASSES")
                self.known_cache_classes.update(custom_cache_classes)

            if hasattr(module, "CUSTOM_AUTH_CLASSES"):
                custom_auth_classes = getattr(module, "CUSTOM_AUTH_CLASSES")
                self.known_auth_classes.update(custom_auth_classes)
            
        for resolver_config in self.known_resolvers:
            OmegaConf.register_new_resolver(resolver_config.name, resolver_config.func, replace=True, use_cache=resolver_config.use_cache)

    def call_delayed_resolver(self, class_name_str: str, *, _parent_):
        return DelayedCallable(
            func=self.call_by_type_name_resolver,
            class_name_str=class_name_str,
            _parent_=_parent_
        )

    def get_known_cache_class(self, name: str):
        if name is None:
            return None
        cache_class = self.known_cache_classes.get(name.lower())
        if cache_class is None:
            raise Exception(f"Cache class mapping not known: '{name}'")
        return cache_class
    
    def call_known_auth_class(self, name: str, *, _parent_):
        if name is None:
            return None
        auth_class = self.known_auth_classes.get(name.lower())
        if auth_class is None:
            raise Exception(f"Authentication class mapping not known: '{name}'")
        
        return self.call_delayed_resolver(
            class_name_str=auth_class,
            _parent_=_parent_
        )
        # return self.call_by_type_name_resolver(auth_class, _parent_=_parent_)

    def _get_callable_by_name(self, class_name_str: str):
        if class_name_str is None:
            return None
        known_callable = self.known_callables.get(class_name_str.lower())
        if known_callable is not None:
            return known_callable
        
        if self.disable_unregistered_callables:
            raise Exception(f"There is no known callable '{class_name_str.lower()}'. Unregistered callables are disabled.")

        return self._get_callable_from_module_by_name(class_name_str)


    def _get_callable_from_module_by_name(self, class_name_str: str):
        try:
            module_name, class_path = class_name_str.split('.', 1)
            if module_name == self.plugins_module_name:
                # load callable from plugins folder
                module = self.plugins_module
                if module is None:
                    logging.error("Plugins not loaded.")
                    raise ImportError("Plugins not loaded.")
                attr_retriever = attrgetter(class_path)
                return attr_retriever(module)
            else:
                # load callable from installed library by importing submodule
                module_path, class_name = class_name_str.rsplit('.', 1)
                module = self._get_module_by_name(module_path)
                return getattr(module, class_name)    
        except (ImportError, AttributeError) as e:
            raise ImportError(class_name_str, e)

    def _get_module_by_name(self, name: str):
        module = import_module(name)
        return module

    def _load_delayed_param(self, obj):
        if isinstance(obj, DelayedCallable):
            return obj.value
        else:
            return obj

    def _load_delayed_params(self, args, kwargs):
        loaded_args = []
        loaded_kwargs = {}
        if args:
            loaded_args = [self._load_delayed_param(x) for x in args]
        if kwargs:
            loaded_kwargs = {k: self._load_delayed_param(v) for k, v in kwargs.items()}
        return (loaded_args, loaded_kwargs)

    def _call_by_type_name(self, class_name_str: Union[Callable, str], call_params: CallResolverParams):
        callable_or_class = (class_name_str if isinstance(class_name_str, Callable)
                                else self._get_callable_by_name(class_name_str))
        if call_params.method is None:
            args, kwargs = self._load_delayed_params(
                call_params.args,
                call_params.kwargs
            )
            result = callable_or_class(*args, **kwargs)
        else:
            args, kwargs = self._load_delayed_params(
                call_params.init_params.args,
                call_params.init_params.kwargs
            )
            class_instance = callable_or_class(*args, **kwargs)
            callable_method = getattr(class_instance, call_params.method)
            args, kwargs = self._load_delayed_params(
                call_params.args,
                call_params.kwargs
            )
            result = callable_method(*args, **kwargs)
        return result

    def _load_from_cache_config(self, cache_config: CacheProviderParams):
        if not(cache_config.required) and (self.force_reload or self.no_cache):
            return None
        
        class_name_str = cache_config.provider
        call_params = cache_config.model_copy(deep=True)
        call_params.method = call_params.get_method
        if call_params.get_params:
            call_params.args = call_params.get_params.args
            call_params.kwargs = call_params.get_params.kwargs
        call_params.kwargs["name"] = cache_config.name
        return self._call_by_type_name(class_name_str, call_params)

    def _save_to_cache_config(self, cache_config: CacheProviderParams, value: Any):
        if not(cache_config.required) and self.no_cache:
            return None
        class_name_str = cache_config.provider
        call_params = cache_config.model_copy(deep=True)
        call_params.method = call_params.set_method
        if call_params.set_params:
            call_params.args = call_params.set_params.args
            call_params.kwargs = call_params.set_params.kwargs
        call_params.kwargs["name"] = cache_config.name
        call_params.kwargs["value"] = value
        return self._call_by_type_name(class_name_str, call_params)
    
    def _delete_from_cache_config(self, cache_config: CacheProviderParams):
        class_name_str = cache_config.provider
        call_params = cache_config.model_copy(deep=True)
        call_params.method = call_params.delete_method
        if call_params.set_params:
            call_params.args = call_params.set_params.args
            call_params.kwargs = call_params.set_params.kwargs
        call_params.kwargs["name"] = cache_config.name
        try:
            self._call_by_type_name(class_name_str, call_params)
        except Exception as ex:
            logging.error(str(ex))

    def _load_from_cache(self, call_params: CallResolverParams) -> Tuple[Union[None, str], Union[None, Any]]:
        if call_params.cache:
            # sort cache configs by name
            ordered_cache_configs = OrderedDict(sorted(call_params.cache.items()))
            for cache_name, cache_config in ordered_cache_configs.items():
                result = self._load_from_cache_config(cache_config)
                if result is not None:
                    return (cache_name, result)
        return (None, None)
    
    def _save_to_cache(self, call_params: CallResolverParams, value: Any, stop_at_cache_name: str = None):
        if call_params.cache:
            # sort cache configs by name
            ordered_cache_configs = OrderedDict(sorted(call_params.cache.items()))
            for cache_name, cache_config in ordered_cache_configs.items():
                if (stop_at_cache_name is not None) and (stop_at_cache_name == cache_name):
                    break
                self._save_to_cache_config(cache_config, value)

    def _delete_from_cache(self, call_params: CallResolverParams):
        if call_params.cache:
            # sort cache configs by name
            ordered_cache_configs = OrderedDict(sorted(call_params.cache.items()))
            for cache_name, cache_config in ordered_cache_configs.items():
                self._delete_from_cache_config(cache_config)

    def call_by_type_name_resolver(self, class_name_str: str, *, _parent_):
        call_params = CallResolverParams.model_validate(_parent_)
        
        result = None
        result_from_cache_name = None
        
        if self.flush_caches:
            self._delete_from_cache(call_params)
        else:
            # try loading from cache
            result_from_cache_name, result = self._load_from_cache(call_params)
        
        # even if flush caches is called, reload value from source to make sure that all downstream resolvers are called and caches are flushed for these as well
        if result is None:
            # value not found in cache - retrieve from source
            result = self._call_by_type_name(class_name_str, call_params)
            if call_params.selector is not None:
                # apply jmespath selector to filter parts of response
                result = jmespath.search(call_params.selector, result)
            
        if not(self.flush_caches):
            # update cache
            self._save_to_cache(call_params, result, result_from_cache_name)
        
        if call_params.as_container:
            # use OmegaConf standard oc.create resolver to convert value to oc config node
            result = oc.create(result, _parent_)
        
        return result