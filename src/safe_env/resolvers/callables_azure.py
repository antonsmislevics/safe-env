import urllib.parse
from typing import Any, Dict, List
import re
import json
import requests
from azure.keyvault.secrets import SecretClient
from azure.keyvault.certificates import CertificateClient

from ..models import (
    AzureKeyVaultCertificate,
    AzureKeyVaultKey
)



def get_azure_key_vault_secrets(
    url: str,
    credential: Any,
    names: List[str],
    include_properties: bool = False
) -> Dict[str, Any]:
    if names is None:
        return None
    
    result = dict()

    client = SecretClient(vault_url=url, credential=credential)
    for name in names:
        value = None
        secret = client.get_secret(name)
        if secret is not None:
            if include_properties:
                value = AzureKeyVaultKey.model_validate(
                    secret,
                    from_attributes=True
                ).model_dump_json()        # ensures that the output can later be cached with regular json serializer
                value = json.loads(value)
            else:
                value = secret.value        
        result[name] = value
    return result

def get_azure_key_vault_certificates(
    url: str,
    credential: Any,
    names: List[str]
) -> Dict[str, Dict[str, Any]]:
    if names is None:
        return None
    
    result = dict()

    certificate_client = CertificateClient(vault_url=url, credential=credential)
    secret_client = SecretClient(vault_url=url, credential=credential)

    for cert_name in names:
        certificate = certificate_client.get_certificate(cert_name)
        secret_parts_match = re.search(r'^https://[^/]+/secrets/([^/]+)/([^/]+)$', certificate.secret_id)
        if secret_parts_match is None:
            raise Exception("Secret id cannot be parsed.")
        
        secret_name = secret_parts_match[1]
        secret_version = secret_parts_match[2]
        secret = secret_client.get_secret(secret_name, secret_version)
        certificate_thumbprint = certificate.properties.x509_thumbprint.hex()
        certificate_private_key = secret.value

        value = AzureKeyVaultCertificate(
            name=cert_name,
            thumbprint=certificate_thumbprint,
            private_key=certificate_private_key
        ).model_dump_json()                 # ensures that the output can later be cached with regular json serializer
        value = json.loads(value)
        result[cert_name] = value

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
