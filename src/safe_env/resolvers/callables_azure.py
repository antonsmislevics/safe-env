import urllib.parse
from typing import Any, Dict, List

import requests
from azure.keyvault.secrets import SecretClient


def get_azure_key_vault_secrets(
    url: str,
    credential: Any,
    names: List[str]
) -> Dict[str, Any]:
    if names is None:
        return None
    
    result = dict()

    client = SecretClient(vault_url=url, credential=credential)
    for name in names:
        value = None
        secret = client.get_secret(name)
        if secret is not None:
            value = secret.value        
        result[name] = value
    return result


AZURE_MANAGEMENT_SCOPE = "https://management.core.windows.net/.default"
AZURE_MANAGEMENT_URL = "https://management.azure.com"
def get_azure_rest_resource(
    url: str,
    credential: Any,
    method: str = "GET",
    timeout: int = 30
) -> Dict[str, Any]:
    url = urllib.parse.urljoin(AZURE_MANAGEMENT_URL, url)
    credential_token = credential.get_token(AZURE_MANAGEMENT_SCOPE)
    headers = {"Authorization": 'Bearer ' + credential_token.token}
    resp = requests.request(method=method, url=url, headers=headers, timeout=timeout)
    return resp.json()
