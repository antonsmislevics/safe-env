from typing import Any

from azure.identity import (
    AzureCliCredential,
    DefaultAzureCredential,
    DeviceCodeCredential,
    InteractiveBrowserCredential,
    ManagedIdentityCredential,
    VisualStudioCodeCredential,
)

from .auth_keeper import get_keeper_login_params


def get_azure_credential_token(credential: Any, scope: str):
    credential_token = credential.get_token(scope)
    return credential_token

KNOWN_AUTH_CLASSES = {
    "azure.default": DefaultAzureCredential,
    "azure.cli": AzureCliCredential,
    "azure.interactive": InteractiveBrowserCredential,
    "azure.managedidentity": ManagedIdentityCredential,
    "azure.devicecode": DeviceCodeCredential,
    "azure.vscode": VisualStudioCodeCredential,
    "azure.token": get_azure_credential_token,
    "keeper": get_keeper_login_params
}
