# Safe Environment Manager (safe-env)
*Safe Environment Manager* allows to manage secrets in environment variables in a safe way.
To achieve this, safe-env follows a set of principles:
1. Configurations for different environments are stored in a set of yaml files, that have no secrets and can be safely pushed to git repository.
0. Secrets are never written to local files, even temporarily.
0. Secrets are stored in one of the following safe locations:
    - the resource itself (for example, access key in Azure Storage Account configuration);
    - external vault (for example, Azure KeyVault);
    - local keyring;
    - environment variables (in memory).
0. Access to resources and vaults is controlled outside of the tool via standard user authentication mechanisms (for example, `az login` for Azure).

# Getting started
## How to install?
The package is still in active development and can be installed directly from git repository:
```bash
python -m pip install "git+https://github.com/antonsmislevics/safe-env.git#egg=safe-env[local]&subdirectory=src"
```
The package does not require to be installed in the same environment that is used for development. It is recommended to create a seperate python virtual environment and install the package into it.

## How to use?
### Defining environment configuration files
To start using `safe-env` you first need to create environment configuration files. By default the tool looks for these files in *./envs* folder. However, custom path can be provided via `--config-dir` option.

Environment configuration file has several sections:
```yaml
depends_on:     # the list of "parent" environment configurations
config:         # tool specific configurations (for example, local keyring)
parameters:     # parameters used when processing this file
secrets:        # secrets stored in local keyring or external vault
vaults:         # external vaults (for example, Azure KeyVault)
resources:      # external resources (for example, Azure Storage Account)
env:            # environment variables
```

Configuration files can be parametrized using a syntax similar to python format strings. It allows to include the following entities:
- `{PARAM: param_name}` - replaced with a value of a param
- `{ENV: env_var_name}` - replaced with environment variable on the host
- `{SECRET: secret_name}` - replaced with a value of a secret
- `{RESOURCE: resource_name}` - replaced with a value of a resource

Here are three examples of simple configuration files:

**./envs/base.yaml**

This is a base environment configuration file.
```yaml
parameters:
  param1: param1_value
  param2: param2_value
  env_name: base_env
  secret_name: secret1
config:
  keyring:
    service_name: "{PARAM: env_name}_secrets"   # default service name in local keyring
secrets:
  secret1:
    keyring_name: demo_secret1      # secret name in keyring
    local: True                     # the secret is stored only in local keyring
env:
  var1: var1
  var2: "{PARAM: param1} - {PARAM: param2}"
  secret_var: "{SECRET: secret1}"
  dynamic_secret_var: "{SECRET: {PARAM: secret_name}}"
```

**./envs/dev.yaml**

This is a development environment configuration file. It inherits from base and overrides one parameter and one environment variable.
```yaml
depends_on:
  - base
parameters:
  env_name: dev_env     # note that this parameter is used to generate service name in local keyring
env:
  var1: dev_var1
```

**./envs/local.yaml**

This is an example of a configuration file that could be used as an add-on when working behind the proxy.
```yaml
env:
  http_proxy: "http-proxy-value"
  https_proxy: "https-proxy-value"
  no_proxy: "no-proxy-value"
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

Now we can set a value for `secret1` secret in local keyring, simulating that *base* and *dev* environments have different values. This can be done via keyring module used by the tool.

```
$ keyring set base_env_secrets demo_secret1
Password for 'demo_secret1' in 'base_env_secrets': 

$ keyring get base_env_secrets demo_secret1
base_secret_value

$ keyring set dev_env_secrets demo_secret1
Password for 'demo_secret1' in 'dev_env_secrets': 

$ keyring get dev_env_secrets demo_secret1
dev_secret_value
```

Now we can inspect how loaded environment variables for *base* and *dev* environments will look.

```
$ se activate base

var1: var1
var2: param1_value - param2_value
secret_var: base_secret_value
dynamic_secret_var: base_secret_value

$ se activate dev

var1: dev_var1
var2: param1_value - param2_value
secret_var: dev_secret_value
dynamic_secret_var: dev_secret_value
```
And if we are working with *dev* environment behind the proxy, we can add *local* environment configuration as an add-on.
```
$ se activate dev local

var1: dev_var1
var2: param1_value - param2_value
secret_var: dev_secret_value
dynamic_secret_var: dev_secret_value
http_proxy: http-proxy-value
https_proxy: https-proxy-value
no_proxy: no-proxy-value
```

Finally we need to set values of these environment variables in the current working shell. In order to do this, we need to call the tool passing type of a shell as additional parameter.

bash:
```bash
# preview the script
$ se activate dev --bash

export var1="dev_var1";export var2="param1_value - param2_value";export secret_var="dev_secret_value";export dynamic_secret_var="dev_secret_value"

# execute the script
$ eval $(se activate dev --bash)
```
PowerShell:
```powershell
# preview the script
> se activate dev --ps

$env:var1="dev_var1";$env:var2="param1_value - param2_value";$env:secret_var="dev_secret_value";$env:dynamic_secret_var="dev_secret_value"

# execute the script
> Invoke-Expression $(se activate dev --ps)
```
Command Prompt:
```
# preview the script
> se activate dev --cmd

set "var1=dev_var1";set "var2=param1_value - param2_value";set "secret_var=dev_secret_value";set "dynamic_secret_var=dev_secret_value"

# copy/paste to execute the script manually
```

If you work with Docker, you can also generate the file that can pass these environment variables from host to container via docker compose.
```bash
# preview docker compose env file content
$ se activate dev --docker

var1=${var1}
var2=${var2}
secret_var=${secret_var}
dynamic_secret_var=${dynamic_secret_var}

# write to .env file
$ se activate dev --docker > docker-dev.env
```

# Working with secrets
Secrets can be stored in local keyring or external vault. In the previous section we've shown how to use secrets from local keyring. In order to use secrets from external vault, first we need to add vaults section to environment configuration file.
```yaml
vaults:
  KeyVault1:
    type: AzureKeyVault       # only Azure KeyVault is currently supported
    params:
      url: "https://[name].vault.azure.net/"    # vault url
      credential: DefaultAzureCredential        # DefaultAzureCredential or AzureCliCredential 
```
Now we can add a secret that is stored in this KeyVault.
```yaml
secrets:
  secret1:                      # name of the secret
    vault: KeyVault1            # reference to keyvault - optional: if empty, looks for this secret in all registered vaults
    vault_name: secret1         # secret name in keyvault - optional: if empty, the name of the secret is used
    keyring_service_name: service_name1     # service name in local keyring - optional: if empty, default value from keyring configuration is used (config.keyring.service_name)
    keyring_name: secret1       # secret name in local keyring  - optional: if empty, the name of the secret is used
    local: False                # if the secret is stored in local keyring only or not - optional: if empty is set to False
```
Now this secret can be used as `{SECRET: secret1}`. It should be noted, that if there is a reference to the secret that is not registered in `secrets` section, the tool will register it automatically. For example, `{SECRET: secret2}` will be converted to:
```yaml
secrets:
  secret2:
    vault:
    vault_name:
    keyring_service_name:
    keyring_name:
    local:
```

By default, secrets from external vaults get cached in local keyring. When loading the secret for the next time, the tool will first check if the value is already cached in local keyring, and only then go to external vault. However, the tool provides few options that allow to change this behavior.
```
$ se activate --help

Options:
  -f, --force-reload-from-remote  Reload values cached in keyring from global
                                  keyvaults and resources.
  -fs, --force-reload-secrets     Reload values cached in keyring from global
                                  keyvaults.
  -ncs, --no-cache-secrets        Do not save secrets from global keyvaults in
                                  local keyring.
```

Note, that authentication is performed outside of the tool. In order to authenticate to external vaults, you must run `az login` from active shell before running the tool.

# Working with resources
Resources allow to load secrets directly from the resource - for example, access keys from Azure Storage Account. These keys can also be cached in external vault or local keyring.

In order to start using resources, first we need to add a folder `./envs/resource-templates` that will store *resource templates*. Then we can add a yaml file (one or multiple) with configurations for resource templates.

**./envs/resource-templates/templates1.yaml**
```yaml
azure_storage_account_key:      # the name of resources template
  params:                       # default values for params that are used when generating inputs
    subscription_id: 
    resource_group_name: 
    storage_account_name:
    key_index: 0
  type: AzureREST               # currently only AzureREST resource handler is supported
  inputs:                       # inputs to resource handler
    url: "/subscriptions/{PARAM: subscription_id}/resourceGroups/{PARAM: resource_group_name}/providers/Microsoft.Storage/storageAccounts/{PARAM: storage_account_name}/listKeys?api-version=2021-04-01&$expand=kerb"     # resource url
    credential: DefaultAzureCredential      # authentication DefaultAzureCredential or AzureCliCredential
    method: POST        # request method GET or POST
    query: "keys[{PARAM: key_index}].value"        # JMESPath query to extract required information from the response - OPTIONAL: if empty, the full object is returned
```

This template can then be used when defining resources in `resources` section of environment configuration file.
```yaml
params:
  subscription_id: "[subscription_id]"
  resource_group_name: "[resource_group]"
  storage_account_name: "[storage_account]"
resources:
  storage_account_info:
    template: azure_storage_account_key
    params:
      subscription_id: "{PARAM: subscription_id}"
      resource_group_name: "{PARAM: resource_group_name}"
      storage_account_name: "{PARAM: storage_account_name}"
```

Now this resource can be used as `{RESOURCE: storage_account_info}`.

In advanced scenarios, resources can reuse values from other resources. For example, if we want to have both storage account keys available, we could remove `query:` from resource template, so the full object is loaded into `storage_account_info` resource, and add two additional resources.
```yaml
resources:
  key1:
    parent: storage_account_info
    query: "keys[0].value"
  key2:
    parent: storage_account_info
    query: "keys[1].value"
```

Now `{RESOURCE: key1}` and `{RESOURCE: key2}` contain both keys of the storage account.

Finally resource values can be cached as secrets in external vault or local keyring.
```yaml
secrets:
  storage_key1:
    vault: KeyVault1
  storage_key2:
    vault: KeyVault1
resources:
  key1:
    parent: storage_account_info
    query: "keys[0].value"
    cache_secret: storage_key1
  key2:
    parent: storage_account_info
    query: "keys[1].value"
    cache_secret: storage_key2
```

When loading the resource for the next time, the tool will first check if the value is already cached in local keyring or external vault, and only then go to resource itself. However, the tool provides few options that allow to change this behavior.
```
$ se activate --help

Options:
  -f, --force-reload-from-remote  Reload values cached in keyring from global
                                  keyvaults and resources.
  -fr, --force-reload-resources   Reload values cached in keyring and global
                                  keyvaults from resources.
  -ncr, --no-cache-resources      Do not save values loaded from resources in
                                  keyring and global keyvaults.
```

Note, that authentication is performed outside of the tool. In order to authenticate to resources and external vaults, you must run `az login` from active shell before running the tool.
