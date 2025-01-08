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

# Getting started
## How to install?
The package is still in active development and can be installed directly from git repository.

The package does not require to be installed in the same environment that is used for development.

## How to use?
### Defining environment configuration files
To start using `safe-env` you first need to create environment configuration files. By default the tool looks for these files in *./envs* folder. However, custom path can be provided via `--config-dir` option.

Configuration files are based on OmegaConf (https://omegaconf.readthedocs.io, https://github.com/omry/omegaconf), and have only two special sections.
```yaml
depends_on:     # the list of "parent" environment configurations (optional)
envs:           # dictionary with resulting environment variables
```

Configuration files can be parametrized using standard OmegaConf variable interpolation and resolvers.

