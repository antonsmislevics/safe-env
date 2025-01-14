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

When developer is on-boarding to a new project, that uses regular .env files, the process usually looks like this:

![Developing without safe-env](https://github.com/antonsmislevics/safe-env/blob/main/docs/images/developing-without-safe-env.png?raw=true)

There are many steps involved, and a lot of opportunities for secrets to leak along the way. In addition, the secrets end up in unsecure places - local .env file in project folder, or environment variables on development machine.

**safe-env** helps to simplify on-boarding process, and ensure that secrets are stored only in-memory or in secure storage.

![Developing with safe-env](https://github.com/antonsmislevics/safe-env/blob/main/docs/images/developing-with-safe-env.png?raw=true)

This also allows to quickly switch between environments while developing, testing, or using software.

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

When the package is installed, **safe-env** can be invoked from the command line as `se` or as `python -m safe_env`.

To check the version of the tool, run:
```bash
se --version

# or

python -m safe_env --version
```

To get a list of all available commands and options, run:
```bash
se --help

# or

python -m safe_env --help
```

<b>Congratulations!</b> Now you are ready to [create environment configuration files](https://antonsmislevics.github.io/safe-env/working-with-envs/).
