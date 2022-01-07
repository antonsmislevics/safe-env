from abc import abstractmethod
from typing import Dict, Any
from . import BaseResourceHandler
import requests
import urllib.parse


class AzureRESTResourceHandler(BaseResourceHandler):
    def __init__(self, name: str, url: str, method: str, credential: Any):
        super().__init__(name)
        self.credential = credential
        if not(method) or not(method.upper() in ["GET", "POST"]):
            method = "GET"
        else:
            method = method.upper()
        
        self.azure_management_scope = "https://management.core.windows.net/"
        self.azure_management_url = "https://management.azure.com"
        self.url = urllib.parse.urljoin(self.azure_management_url, url)
        self.method = method
        

    def _load_resource(self) -> Dict[str, Any]:
        credential_token = self.credential.get_token(self.azure_management_scope)
        headers = {"Authorization": 'Bearer ' + credential_token.token}
        resp = requests.request(method=self.method, url=self.url, headers=headers)
        return resp.json()

