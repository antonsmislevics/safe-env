# Welcome to Safe Environment Manager (safe-env)
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
