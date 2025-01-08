from .callables_azure import (
    get_azure_key_vault_secrets,
    get_azure_rest_resource
)
from .callables_azuredevops import (
    get_azure_devops_pat
)
from .callables_keyring import (
    get_keyring_secrets
)

KNOWN_CALLABLES = {
    "get_azure_key_vault_secrets": get_azure_key_vault_secrets,
    "get_keyring_secrets": get_keyring_secrets,
    "get_azure_rest_resource": get_azure_rest_resource,
    "get_azure_devops_pat": get_azure_devops_pat
}
