# Developing plugins

Real-life software development projects are very different. It is expected, that **safe-env** users might need to load secrets from various specific sources, use different authentication providers or caches. Also, we plan to expand the list of integrations supported out of the box, we will never be able to cover all scenarios.

That's why **safe-env** comes with built-in support for custom plugins - an easy way to execute your custom Python code when resolving environment configurations.

## Enabling plugins

To start using plugins, you need to create `plugins` subfolder in a folder where your environment configuration files are located and put `__init__.py` file in it:

``` py title="./envs/plugins/__init__.py"
# import required dependecies

CUSTOM_RESOLVERS = []       # register custom OmegaConf resolvers
CUSTOM_CALLABLES = {}       # register custom shortcut names for callables, that can be used with se.call
CUSTOM_AUTH_CLASSES = {}    # register custom shortcut names for auth providers, that can be used with se.auth
CUSTOM_CACHE_CLASSES = {}   # register custom shortcut names for cache providers, that can be used with se.cache
```

## Developing plugins

Now **safe-envs** treats plugins folder as a regular Python module named `_plugins_`. This allows to organize Python code in multiple files and easily invoke it from environment configurations.

Here is an example:
``` py title="./envs/plugins/auth.py"
def my_custom_auth():
    # implementation of custom authentication provider
    return None    # returns some credentials object
```

``` py title="./envs/plugins/call.py"
def my_custom_call():
    # implementation of custom callable to retrieve secrets
    return None    # returns object with secrets
```

``` py title="./envs/plugins/cache.py"
from safe_env.cache_providers import BaseCacheProvider

# implement custom cache provider
class MyCustomCacheProvider(BaseCacheProvider):
    def __init__(self):
        # constructor
        super().__init__()
    
    def _get(self, name: str):
        # get secret
        return None # return retrieved secret or None

    def _set(self, name: str, value: Any):
        # save secret
        pass
    
    def _delete(self, name: str):
        # delete secret
        pass
```

``` py title="./envs/plugins/resolvers.py"
def my_custom_resolver():
    # implementation of custom OmegaConf resolver
    return None     # returns some value
```

``` py title="./envs/plugins/__init__.py"
# import required dependecies
from safe_env.models import ResolverConfiguration
from .auth import my_custom_auth
from .call import my_custom_call
from .cache import MyCustomCacheProvider
from .resolvers import my_custom_resolver

# register custom OmegaConf resolvers
CUSTOM_RESOLVERS = [
    ResolverConfiguration(
        name="my.custom_resolver",
        func=my_custom_resolver,
        use_cache=False
    )
]

# register custom shortcut names for callables, that can be used with se.call
CUSTOM_CALLABLES = {
    "my_custom_call_method": my_custom_call
}

# register custom shortcut names for auth providers, that can be used with se.auth
CUSTOM_AUTH_CLASSES = {
    "my_custom_auth_provider": my_custom_auth
}

# register custom shortcut names for cache providers, that can be used with se.cache
CUSTOM_CACHE_CLASSES = {
    "my_custom_cache": MyCustomCacheProvider
}
```

## Invoking plugins

Now we can invoke plugins from environment configuration files, via OmegaConf resolvers, using custom shortcut names, or full names of callables.

``` yaml title="Invoking custom resolvers"
    value: ${my.custom_resolver:}
```

``` yaml title="Invoking custom callables"
    value: ${se.call:my_custom_call_method}

    # or

    value: ${se.call:_plugins_.my_custom_call}
```

``` yaml title="Invoking custom auth providers"
    value: ${se.auth:my_custom_auth_provider}

    # or

    value: ${se.auth:_plugins_.my_custom_auth}
```

``` yaml title="Invoking custom cache providers"
    # ...
    cache:
      my_cache_name:
        name: my_cache_key
        provider: ${se.cache:MyCustomCacheProvider}
    # ...
    
    # or
    
    # ...
    cache:
      my_cache_name:
        name: my_cache_key
        provider: ${se.cache:_plugins_.MyCustomCacheProvider}
    # ...
```
