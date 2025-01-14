# Working with secrets

In this section we cover how to efficiently handle secrets in environment configuration files using **safe-env**.

## Overview
A set of custom OmegaConf resolvers is included to work with secrets in a secure way:

- `se.call` - allows to invoke any Python callable 
- `se.auth` - shortcut to invoke classes generating credentials for authentication to various sources
- `se.cache` - shortcut to invoke classes providing caching capabilities

It is important to highlight, that all resolvers are implemented in a way that parent config element is used as a container that stores configurations on how callable will be invoked.

Here is a sample configuration file showing how these resolvers work together:
``` yaml linenums="1"
# common params, that are typically overridden in nested configurations
params:
  tenant_id: <tenant-id>
  az_storage_account_name: <storage-account-name>
  kv_url: https://<keyvaylt-name>.vault.azure.net/
  kv_secret_postfix: DEV
  keyring_postfix: dev

# retrieve credentials required for authentication
credentials:
  azure_identity:
    value: ${se.auth:azure.interactive}           # use azure interactive login
    kwargs:
      tenant_id: ${params.tenant_id}
    cache:                                        # cache credentials, so we don't need to login multiple times
      memory:
        name: azure_credential                    # key to be used when storing object in memory
        provider: ${se.cache:memory}              # use in-memory cache
        required: True

# dynamically construct Azure KeyVault secret names for different environments
# in this example we assume that the same KeyVault is used for all environments and different postfixes are used
kv_key_names:
  app_client_id: APPCLIENTID${params.kv_secret_postfix}
  app_client_secret: APPCLIENTSECRET${params.kv_secret_postfix}

# retrieve secret from Azure KeyVault
kv_secrets:
  value: ${se.call:get_azure_key_vault_secrets}     # here we use a registered/known shortcut name for secrets resolver, 
                                                    # but we could also use the full name of the callable instead
  as_container: True                                # convert returned result to OmegaConf container
  kwargs:
    url: ${params.kv_url}
    credential: ${credentials.azure_identity.value} # use credentials for authentication
    names:                                          # names of secrets to retrieve from KeyVault
      - AZSTORAGEACCOUNTKEY
      - ${kv_key_names.app_client_id}
      - ${kv_key_names.app_client_secret}
  cache:
    local_keyring:                                  # cache secrets locally, so we don't need to go to KeyVault every time
      name: kv_secrets_${params.keyring_postfix}    # secret name in the cache
      provider: ${se.cache:keyring}                 # use local keyring as a cache
      init_params:
        kwargs:
          service_name: my_app_secrets              # service name in the cache

# construct final environment variables
envs:                                               
  AZ_ACCOUNT_NAME: ${params.az_storage_account_name}
  AZ_ACCOUNT_KEY: ${kv_secrets.value.AZSTORAGEACCOUNTKEY}
  APP_CLIENT_ID: ${kv_secrets.value.${kv_key_names.app_client_id}}
  APP_CLIENT_SECRET: ${kv_secrets.value.${kv_key_names.app_client_secret}}
```

Running `se resolve` shows how this configuration will be resolved with values:
``` yaml linenums="1"
params:
  tenant_id: <tenant-id>
  az_storage_account_name: <storage-account-name>
  kv_url: https://<keyvaylt-name>.vault.azure.net/
  kv_secret_postfix: DEV
  keyring_postfix: dev
credentials:
  azure_identity:
    value: !<object> 'safe_env.resolvers.delayedcallable.DelayedCallable'
    kwargs:
      tenant_id: <tenant-id>
    cache:
      memory:
        name: azure_credential
        provider: !!python/name:safe_env.cache_providers.memory_cache.MemoryCache ''
        required: true
kv_key_names:
  app_client_id: APPCLIENTIDDEV
  app_client_secret: APPCLIENTSECRETDEV
kv_secrets:
  value:
    AZSTORAGEACCOUNTKEY: <storage-account-key>
    APPCLIENTIDDEV: <app-client-id>
    APPCLIENTSECRETDEV: <app-client-secret>
  as_container: true
  kwargs:
    url: https://<keyvaylt-name>.vault.azure.net/
    credential: !<object> 'safe_env.resolvers.delayedcallable.DelayedCallable'
    names:
    - AZSTORAGEACCOUNTKEY
    - APPCLIENTIDDEV
    - APPCLIENTSECRETDEV
  cache:
    local_keyring:
      name: kv_secrets_dev
      provider: !!python/name:safe_env.cache_providers.keyring_cache.KeyringCache ''
      init_params:
        kwargs:
          service_name: my_app_secrets
envs:
  AZ_ACCOUNT_NAME: <storage-account-name>
  AZ_ACCOUNT_KEY: <storage-account-key>
  APP_CLIENT_ID: <app-client-id>
  APP_CLIENT_SECRET: <app-client-secret>
```

## Loading secrets

Depending on project specifics, secrets may need to be loaded from different sources. For example, if the project is relying on Microsoft Azure cloud infrastructure, secrets may be loaded from Azure KeyVault or directly from Azure resources (for example, access keys to specific resources). **safe-env** supports such scenarios by allowing to invoke arbitrary python code, what gives unlimited integration possibilities.

To invoke custom code from configuration file, `se.call` resolver should be used:

``` yaml linenums="27" hl_lines="3"
# retrieve secret from Azure KeyVault
kv_secrets:
  value: ${se.call:get_azure_key_vault_secrets}     # here we use a registered/known shortcut name for secrets resolver, 
                                                    # but we could also use the full name of the callable instead
  as_container: True                                # convert returned result to OmegaConf container
  kwargs:
    url: ${params.kv_url}
    credential: ${credentials.azure_identity.value} # use credentials for authentication
    names:                                          # names of secrets to retrieve from KeyVault
      - AZSTORAGEACCOUNTKEY
      - ${kv_key_names.app_client_id}
      - ${kv_key_names.app_client_secret}
  cache:
    local_keyring:                                  # cache secrets locally, so we don't need to go to KeyVault every time
      name: kv_secrets_${params.keyring_postfix}    # secret name in the cache
      provider: ${se.cache:keyring}                 # use local keyring as a cache
      init_params:
        kwargs:
          service_name: my_app_secrets              # service name in the cache
```

As argument `se.call` expects full name of a callable, or registered "known" shortcut name. In this case, `get_azure_key_vault_secrets` is known shortcut name for `safe_env.resolvers.callables_azure.get_azure_key_vault_secrets`:
``` py title="./src/safe_env/resolvers/callables_azure.py"
def get_azure_key_vault_secrets(
    url: str,
    credential: Any,
    names: List[str]
) -> Dict[str, Any]:
  # ...
```

**safe-env** comes with a set of "known" shortcut names, which are registered via:

``` py title="./src/safe_env/resolvers/callables.py"
# ...
KNOWN_CALLABLES = {
    "get_azure_key_vault_secrets": get_azure_key_vault_secrets,
    "get_keyring_secrets": get_keyring_secrets,
    "get_azure_rest_resource": get_azure_rest_resource,
    "get_azure_devops_pat": get_azure_devops_pat
}
# ...
```
Usually, a callable expects that specific arguments are provided during invocation. For example, `get_azure_key_vault_secrets` expects that three arguments are provided: url, credential and names of secrets. `se.call` allows to provide these arguments via `args` and `kwargs` attributes under the same parent in configuration file:
``` yaml linenums="27" hl_lines="6-12"
# retrieve secret from Azure KeyVault
kv_secrets:
  value: ${se.call:get_azure_key_vault_secrets}     # here we use a registered/known shortcut name for secrets resolver, 
                                                    # but we could also use the full name of the callable instead
  as_container: True                                # convert returned result to OmegaConf container
  kwargs:
    url: ${params.kv_url}
    credential: ${credentials.azure_identity.value} # use credentials for authentication
    names:                                          # names of secrets to retrieve from KeyVault
      - AZSTORAGEACCOUNTKEY
      - ${kv_key_names.app_client_id}
      - ${kv_key_names.app_client_secret}
  cache:
    local_keyring:                                  # cache secrets locally, so we don't need to go to KeyVault every time
      name: kv_secrets_${params.keyring_postfix}    # secret name in the cache
      provider: ${se.cache:keyring}                 # use local keyring as a cache
      init_params:
        kwargs:
          service_name: my_app_secrets              # service name in the cache
```

This callable will return a dictionary with names/values for each secret name. However, this dictionary is not a valid OmegaConf container. `as_container: True` attribute tells `se.call` that we want to convert returned object to a valid container. This allows us to use values from it as:
``` yaml
  AZ_ACCOUNT_KEY: ${kv_secrets.value.AZSTORAGEACCOUNTKEY}
```
Alternatively, if not all values returned by the callable are required, it is possible to apply [JMESPath expression](https://jmespath.org) on returned value, via `selector` attribute:
``` yaml hl_lines="3"
  # ...
  value: ${se.call:some_method}
  selector: "<JMESPath expression to apply on returned value>"
  # ...
```

Finally, in more complex scenarios, we may want `se.call` to initialize an instance of the class first, and then invoke specific method from this class. This can be achieved by using the following attributes:
``` yaml
  # ...
  value: ${se.call:<full name of the class>}  # full name of the class as a callable passed to se.call
  init_params:    # parameters passed to constructor
    args:         # list of args for constructor
    kwargs:       # dictionary with kwargs for constructor
  method:         # name of the method to invoke from class instance
  args:           # list of args for method
  kwargs:         # dictionary with kwargs for method
  # ...
```

## Caching

Typically, secrets do not change every day. That's why, to improve developer experience, it may be good to cache them in a secure local storage. Good common choice is to use local keyring - the same storage, that operating system uses to store user secrets.

**safe-env** allows to cache retrieved secrets via `cache` attribute:
``` yaml linenums="27" hl_lines="13-19"
# retrieve secret from Azure KeyVault
kv_secrets:
  value: ${se.call:get_azure_key_vault_secrets}     # here we use a registered/known shortcut name for secrets resolver, 
                                                    # but we could also use the full name of the callable instead
  as_container: True                                # convert returned result to OmegaConf container
  kwargs:
    url: ${params.kv_url}
    credential: ${credentials.azure_identity.value} # use credentials for authentication
    names:                                          # names of secrets to retrieve from KeyVault
      - AZSTORAGEACCOUNTKEY
      - ${kv_key_names.app_client_id}
      - ${kv_key_names.app_client_secret}
  cache:
    local_keyring:                                  # cache secrets locally, so we don't need to go to KeyVault every time
      name: kv_secrets_${params.keyring_postfix}    # secret name in the cache
      provider: ${se.cache:keyring}                 # use local keyring as a cache
      init_params:
        kwargs:
          service_name: my_app_secrets              # service name in the cache
```

The attribute allows to specify one or multiple caches as a dictionary. If multiple caches are configured, they will be treated as being ordered alphabetically by dictionary key.

For each cache we must specify:

-  `name` - the name that will be used to store secret in the cache
- `provider` - `se.cache` resolver with a full name of a callable, or registered "known" shortcut cache name.

In this case, `keyring` is a known shortcut name for `safe_env.cache_providers.AzureKeyVaultSecretCache`:
``` py title="./src/cache_providers/keyring_cache.py"
# ...
from .base_cache_provider import BaseCacheProvider

class KeyringCache(BaseCacheProvider):
    def __init__(self, keyring_type: str = None, service_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.keyring_type = keyring_type
        self.default_service_name = service_name
# ...
```

**safe-env** comes with a set of "known" shortcut cache names, which are registered via:

``` py title="./src/safe_env/resolvers/cache.py"
# ...
KNOWN_CACHE_CLASSES = {
    "memory": cache_providers.MemoryCache,
    "keyring": cache_providers.KeyringCache,
    "azure.keyvault": cache_providers.AzureKeyVaultSecretCache
}
# ...
```

Constructor of cache provider class may expect, that specific arguments are provided. For example, `KeyringCache` expects that `service_name` is provided. Same as with `se:call` this can be done via:
``` yaml
  # ...
  init_params:    # parameters passed to constructor
    args:         # list of args for constructor
    kwargs:       # dictionary with kwargs for constructor
  # ...
```

**safe-env** comes with few commands / options that help to manage caches:
``` bash
$ se flush    # Delete values stored in all caches for specified environments.

$ se (resolve | activate | run) (--force-reload | -f)   # Ignore all cached values and reload from sources.

$ se (resolve | activate | run) (--no-cache | -n)   # Do not use caches to load/save values.
```

However, some caches are "technical" and should always be used - for example, in-memory cache for storing authentication credentials. To achieve this, we can mark specific cache as `required`:
``` yaml linenums="9" hl_lines="11"
  # retrieve credentials required for authentication
credentials:
  azure_identity:
    value: ${se.auth:azure.interactive}           # use azure interactive login
    kwargs:
      tenant_id: ${params.tenant_id}
    cache:                                        # cache credentials, so we don't need to login multiple times
      memory:
        name: azure_credential                    # key to be used when storing object in memory
        provider: ${se.cache:memory}              # use in-memory cache
        required: True
```

## Authentication

Usually, retrieving secrets requires some form of authentication. For example, if secrets are stored in Azure, the user is required to authenticate via `az login` or interactive browser login.

**safe-env** allows to invoke a callable to retrieve authentication credentials via `se.auth` resolver:
``` yaml linenums="9" hl_lines="4"
  # retrieve credentials required for authentication
credentials:
  azure_identity:
    value: ${se.auth:azure.interactive}           # use azure interactive login
    kwargs:
      tenant_id: ${params.tenant_id}
    cache:                                        # cache credentials, so we don't need to login multiple times
      memory:
        name: azure_credential                    # key to be used when storing object in memory
        provider: ${se.cache:memory}              # use in-memory cache
        required: True
```

As argument `se.auth` expects a full name of a callable, or registered "known" shortcut auth provider name. In this case, `azure.interactive` is a known shortcut name for `azure.identity.InteractiveBrowserCredential`.

**safe-env** comes with a set of "known" shortcut auth provider names, which are registered via:

``` py title="./src/safe_env/resolvers/auth.py"
# ...
KNOWN_AUTH_CLASSES = {
    "azure.default": DefaultAzureCredential,
    "azure.cli": AzureCliCredential,
    "azure.interactive": InteractiveBrowserCredential,
    "azure.managedidentity": ManagedIdentityCredential,
    "azure.devicecode": DeviceCodeCredential,
    "azure.vscode": VisualStudioCodeCredential,
    "azure.token": get_azure_credential_token
}
# ...
```

Arguments to auth provider can be provided via:
``` yaml
  # ...
  args:           # list of args
  kwargs:         # dictionary with kwargs
  # ...
```

Since the same credentials might be used multiple times, while resolving configuration file, it is a good idea to cache them in-memory:

``` yaml linenums="9" hl_lines="7-11"
  # retrieve credentials required for authentication
credentials:
  azure_identity:
    value: ${se.auth:azure.interactive}           # use azure interactive login
    kwargs:
      tenant_id: ${params.tenant_id}
    cache:                                        # cache credentials, so we don't need to login multiple times
      memory:
        name: azure_credential                    # key to be used when storing object in memory
        provider: ${se.cache:memory}              # use in-memory cache
        required: True
```

!!! info "Interesting Fact"

    Technically `se.auth` is not a regular callable, but `safe_env.resolvers.delayedcallable.DelayedCallable`. It is invoked only when authentication credentials are really needed. For example, if secrets can be retrieved from the cache, `se.auth` will not ask the user for authentication credentials.

<b>Congratulations!</b> Now you know all moving parts, and are ready to integrate **safe-env** with custom secret sources, authentication providers, or caches by [implementing plugins](plugins.md).


