# Safe Environment Manager (safe-env)
*Safe Environment Manager* allows to manage secrets in environment variables in a safe way.
To achieve this, safe-env follows a set of principles:
1. Configurations for different environments are stored in a set of yaml files, that have no secrets and can be safely pushed to git repository.
0. Secrets are never written to local files, even temporarily (Note: also it is possible to save the output in the file, this is not recommended, and should be considered only as an exception for short term temporary use).
0. Secrets are stored in one of the following safe locations:
    - the resource itself (for example, access key in Azure Storage Account configuration);
    - external vault (for example, Azure KeyVault);
    - local keyring;
    - environment variables (in memory).
0. Access to required resources and vaults is controlled via standard user authentication mechanisms (for example, `az login` or interactive browser login for Azure).

More info:
- Documentation: https://antonsmislevics.github.io/safe-env
- Repository: https://github.com/antonsmislevics/safe-env

# Getting started
## How to install?
The package can be installed using pip:
```bash
python -m pip install safe-env
```

If using uv, it can be installed globally as a tool or as a dev dependency in specific project:
```bash
# install as a tool
uv tool safe-env

# or add as dev dependency
uv add safe-env --dev
```

Latest dev version can also be installed directly from git repository:
```bash
# pip
python -m pip install git+https://github.com/antonsmislevics/safe-env.git

# uv as a tool
uv tool install git+https://github.com/antonsmislevics/safe-env.git

# uv as dev dependency
uv add git+https://github.com/antonsmislevics/safe-env.git --dev
```

The package does not require to be installed in the same virtual environment that is used for development.

## How to use?
### Defining environment configuration files
To start using `safe-env` you first need to create environment configuration files. By default the tool looks for these files in *./envs* folder. However, custom path can be provided via `--config-dir` option.

Configuration files are based on OmegaConf (https://omegaconf.readthedocs.io, https://github.com/omry/omegaconf), and have only two special sections.
```yaml
depends_on:     # the list of "parent" environment configurations (optional)
envs:           # dictionary with resulting environment variables
```

Configuration files can be parametrized using standard OmegaConf variable interpolation and resolvers.

Here are three examples of simple configuration files. To keep things simple, we are not loading any secrets yet - this will be covered later.

**./envs/base.yaml**

This is a base environment configuration file.
```yaml
params:
  param1: param1_value
  param2: param2_value
  param3: param3_value
  env_name: base_env
envs:
  var1: var1
  var2: "${params.param1} - ${params.param2}"
  var3: ${params.param3}
  env_name: ${params.env_name}
```

**./envs/dev.yaml**

This is a development environment configuration file. It inherits from base and overrides one parameter and one environment variable.
```yaml
depends_on:
  - base
params:
  env_name: dev_env
envs:
  var1: dev_var1
```

**./envs/local.yaml**

This is an example of a configuration file that could be used as an add-on when working in corporate environment behind the proxy.
```yaml
envs:
  http_proxy: "http-proxy-url"
  https_proxy: "https-proxy-url"
  no_proxy: "no-proxy-configuration"
```

### Loading environment
The tool can be invoked as `se` or as `python -m safe_env`.

First, lets list available environment configurations:


```
$ se list

+-------+-----------------+
| Name  |      Path       |
+-------+-----------------+
| base  | envs/base.yaml  |
|  dev  |  envs/dev.yaml  |
| local | envs/local.yaml |
+-------+-----------------+
```

Now we can inspect how loaded environment variables for *base* and *dev* environments will look.

```
$ se activate base

var1: var1
var2: param1_value - param2_value
var3: param3_value
env_name: base_env

$ se activate dev

var1: dev_var1
var2: param1_value - param2_value
var3: param3_value
env_name: dev_env

```

And if we are working with *dev* environment behind the proxy, we can add *local* environment configuration as an add-on.

```
$ se activate dev local

var1: dev_var1
var2: param1_value - param2_value
var3: param3_value
env_name: dev_env
http_proxy: http-proxy-url
https_proxy: https-proxy-url
no_proxy: no-proxy-configuration

```

Finally we need to set values of these environment variables in the current working shell or in the process where our application will be executed. There are two ways do this.

#### Option 1: Run process / application with loaded environment variables
First, we can call `se run` to run another process / application with loaded environment variables.

For example:
```bash
# run printenv to show which environment variables are set in sub process
# NOTE: --no-host-envs option specifies that other environment variables from the host will not be available to sub process
$ se run dev --no-host-envs --cmd "printenv"

var1=dev_var1
var2=param1_value - param2_value
var3=param3_value
env_name=dev_env

```

If another application is a Python module, we can run it with `--python-module` or `-py` option:
```bash
$ se run dev --no-host-envs -py --cmd "uvicorn my_fastapi_webapp.app:app --reload --port 8080 --host 0.0.0.0"
```
In this case `se` will configure environment variables and invoke this module in the same process. As a result, for example, the following debug configuration in VSCode launch.json will start web application with environment variables for `dev` configuration and attach debugger:
```json
...
{
    "name": "Debug FastAPI with dev env variables",
    "type": "debugpy",
    "request": "launch",
    "module": "safe_env",
    "args": ["run", "dev", "-py", "--cmd", "uvicorn my_fastapi_webapp.app:app --reload --port 8080 --host 0.0.0.0"],
    "cwd": "${workspaceFolder}"
}
...
```

#### Option 2: Set environment variables in current shell or generate the file for use with docker
Second, we can call `se activate` passing a type of a shell as additional parameter. This allows to generate scripts that can be used to set environment variables in the current shell session.

bash:
```bash
# preview the script
$ se activate dev --bash

export var1="dev_var1";export var2="param1_value - param2_value";export var3="param3_value";export env_name="dev_env"

# execute the script to set env variables
$ eval $(se activate dev --bash)

```
PowerShell:
```powershell
# preview the script
> se activate dev --ps

$env:var1="dev_var1";$env:var2="param1_value - param2_value";$env:var3="param3_value";$env:env_name="dev_env"

# execute the script
> Invoke-Expression $(se activate dev --ps)

```
Command Prompt:
```
# preview the script
> se activate dev --cmd

set "var1=dev_var1";set "var2=param1_value - param2_value";set "var3=param3_value";set "env_name=dev_env"

# copy/paste to execute the script manually

```

If you work with Docker, you can also generate the file that can pass these environment variables from host to container via docker compose.
```bash
# preview docker compose env file content
$ se activate dev --docker

var1=${var1}
var2=${var2}
var3=${var3}
env_name=${env_name}

# write to .env file
$ se activate dev --docker --out docker-dev.env

```

Finally, you can generate `.env` file containing all values, and use it with Docker or other tools.
```bash
# preview env file content
$ se activate dev --env

var1=dev_var1
var2=param1_value - param2_value
var3=param3_value
env_name=dev_env

# write to .env file
$ se activate dev --env --out dev.env

```

**IMPORTANT:** Please note that since this file will contain all values (including secrets) it is recommended to: 1) use such files only if there is no option to load values from in-memory environment variables; 2) delete this file immediately after use.

### Developing and debugging more complex config files
Configs in previous examples were simple. When developing more complex configs `se resolve` command helps to debug variable interpolation and resolvers. It returns the entire config yaml file, with all values resolved.

```bash
# debug dev configuration
$ se resolve dev

params:
  param1: param1_value
  param2: param2_value
  param3: param3_value
  env_name: dev_env
envs:
  var1: dev_var1
  var2: param1_value - param2_value
  var3: param3_value
  env_name: dev_env

# debug dev+local configuration
$ se resolve dev local

params:
  param1: param1_value
  param2: param2_value
  param3: param3_value
  env_name: dev_env
envs:
  var1: dev_var1
  var2: param1_value - param2_value
  var3: param3_value
  env_name: dev_env
  http_proxy: http-proxy-url
  https_proxy: https-proxy-url
  no_proxy: no-proxy-configuration

```

# Working with secrets
A set of custom OmegaConf resolvers is included to work with secrets in a secure way:
- `se.auth` - shortcut to invoke classes generating credentials for authentication to various sources
- `se.call` - allows to invoke any Python callable 
- `se.cache` - shortcut to invoke classes providing caching capabilities

It is important to highlight, that all resolvers are implemented in a way that parent config element is used as a container that stores configurations on how callable will be invoked.

Here is a sample configuration file showing how these resolvers work together:
```yaml
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
```yaml
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

