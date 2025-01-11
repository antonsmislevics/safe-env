# Working with environments

In this section we cover how to define and use environment configuration files for **safe-env**.

## How to define environments?
To start using **safe-env** you first need to create environment configuration files. By default the tool looks for these files in *./envs* folder. However, custom path can be provided via `--config-dir` option.

Configuration files are based on [OmegaConf](https://omegaconf.readthedocs.io), and have only two special sections:
```yaml
depends_on:     # the list of "parent" environment configurations (optional)
envs:           # dictionary with resulting environment variables
```

Configuration files can be parametrized using standard OmegaConf variable interpolation and resolvers.

Here are three examples of simple configuration files. To keep things simple, we are not loading any secrets yet - this will be covered later.

This is a base environment configuration file.
``` yaml title="./envs/base.yaml"
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

This is a development environment configuration file. It inherits from base and overrides one parameter and one environment variable.
``` yaml title="./envs/dev.yaml"
depends_on:
  - base
params:
  env_name: dev_env
envs:
  var1: dev_var1
```

This is an example of a configuration file that could be used as an add-on when working in corporate environment behind the proxy.
``` yaml title="./envs/local.yaml"
envs:
  http_proxy: "http-proxy-url"
  https_proxy: "https-proxy-url"
  no_proxy: "no-proxy-configuration"
```

## How to load environment?

First, let's list available environment configurations:


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

Now we can inspect how loaded environment variables for *base* and *dev* environments look.

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

Finally, we need to set values of these environment variables in the current working shell or in the process where our application will be executed. Depending on your situation, there are several ways do this.

### Option 1: Run process / application

First, we can call `se run` to run another process / application with loaded environment variables.

For example:
```bash
# run printenv to show which environment variables are set in sub process
# NOTE: --no-host-envs option specifies that other environment variables from the host will not be available to subprocess
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

In this case **safe-env** will configure environment variables and invoke this module in the same process. As a result, the following debug configuration in VSCode *launch.json* will start web application with environment variables for *dev* configuration and attach a debugger:

``` json title=".vscode/launch.json"
// ... 
{
    "name": "Debug FastAPI with dev env variables",
    "type": "debugpy",
    "request": "launch",
    "module": "safe_env",
    "args": ["run", "dev", "-py", "--cmd", "uvicorn my_fastapi_webapp.app:app --reload --port 8080 --host 0.0.0.0"],
    "cwd": "${workspaceFolder}"
}
// ... 
```

### Option 2: Set environment variables in current shell

Second, we can call `se activate` passing a type of a shell as additional parameter. This allows to generate scripts that can be used to set environment variables in the current shell session.

=== "bash"

    ``` bash
    # preview the script
    $ se activate dev --bash

    export var1="dev_var1";export var2="param1_value - param2_value";export var3="param3_value";export env_name="dev_env"

    # execute the script to set env variables
    $ eval $(se activate dev --bash)
    ```

=== "PowerShell"

    ``` powershell
    # preview the script
    > se activate dev --ps

    $env:var1="dev_var1";$env:var2="param1_value - param2_value";$env:var3="param3_value";$env:env_name="dev_env"

    # execute the script
    > Invoke-Expression $(se activate dev --ps)
    ```

=== "Command Prompt"

    ```
    # preview the script
    > se activate dev --cmd

    set "var1=dev_var1";set "var2=param1_value - param2_value";set "var3=param3_value";set "env_name=dev_env"

    # copy/paste to execute the script manually
    ```

### Option 3: Generate .env file for Docker

If you work with Docker, you have several options:

1. Pass names of environment variables as command line arguments to `docker run`:
``` bash
$ se run dev --cmd "docker run -it --rm -e var1 -e var2 -e var3 -e env_name python:3.10-slim-buster printenv"
```
2. Pass names of environment variables via .env file to `docker run`:
``` bash
$ se run dev --cmd "docker run -it --rm --env-file docker.env python:3.10-slim-buster printenv"
```
3. Pass names of environment variables in `docker-compose.yaml`:
``` yaml title="docker-compose.yaml" hl_lines="5-9"
services:
  python:
    image: python:3.10-slim-buster
    command: printenv
    environment:
      - var1
      - var2
      - var3
      - env_name
```
``` bash
se run dev -c "docker compose up"
```
4. Pass names of environment variables via .env file to `docker compose`:
``` yaml title="docker-compose.yaml" hl_lines="5"
services:
  python:
    image: python:3.10-slim-buster
    command: printenv
    env_file: docker.env
```
``` bash
se run dev -c "docker compose up"
```

**safe-env** can automatically generate `docker.env` file mentioned above.
```bash
# preview docker env file content
$ se activate dev --docker

var1
var2
var3
env_name

# write to .env file
$ se activate dev --docker --out docker.env
```

### Option 4: Generate regular .env file (not recommended)

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

!!! danger "Important"

    Please note that since this file will contain all values, including secrets, it is recommended to:

      1. use such files only if there is no option to load values from in-memory environment variables;
      2. delete this file immediately after use.


## How to define/debug more complex config files?
Configs in previous examples were simple. When defining more complex configs `se resolve` command helps to debug variable interpolation and resolvers. It returns the entire config yaml file, with all values resolved.

=== "Debug dev configuration"

    ```bash
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
    ```

=== "Debug dev+local configuration"

    ```bash
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

<b>Congratulations!</b> Now you are ready to [start loading secrets](working-with-secrets.md).
