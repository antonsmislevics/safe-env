from .callables_azure import (
    get_azure_key_vault_secrets,
    get_azure_key_vault_certificates,
    get_azure_rest_resource
)
from .callables_azuredevops import (
    get_azure_devops_pat
)
from .callables_keyring import (
    get_keyring_secrets
)
from .callables_keeper import (
    get_keeper_secrets,
    get_keeper_secrets_by_uids
)

KNOWN_CALLABLES = {
    "get_azure_key_vault_secrets": get_azure_key_vault_secrets,
    "get_azure_key_vault_certificates": get_azure_key_vault_certificates,
    "get_keyring_secrets": get_keyring_secrets,
    "get_azure_rest_resource": get_azure_rest_resource,
    "get_azure_devops_pat": get_azure_devops_pat,
    "get_keeper_secrets": get_keeper_secrets,
    "get_keeper_secrets_by_uids": get_keeper_secrets_by_uids
}
