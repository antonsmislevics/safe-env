import urllib.parse

import keyring
from pydantic import BaseModel


class AzureDevOpsPAT(BaseModel):
    username: str
    password: str
    url: str

def get_azure_devops_pat(
    index_url: str
) -> AzureDevOpsPAT:
    if index_url is None:
        return None

    creds = keyring.get_credential(index_url, None)
    if creds is None:
        raise Exception(f"Cannot retrieve Azure DevOps PAT for {index_url}")
    
    parsed_index_url = urllib.parse.urlparse(index_url)
    username = parsed_index_url.username or 'azure'
    password = creds.password
    hostname = parsed_index_url.hostname
    parsed_index_url_with_creds = parsed_index_url._replace(netloc=f"{username}:{password}@{hostname}")
    return AzureDevOpsPAT(
        username=creds.username,
        password=creds.password,
        url=urllib.parse.urlunparse(parsed_index_url_with_creds)
    )