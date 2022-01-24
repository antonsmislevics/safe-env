import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict


class LocalKeyringSettings(BaseModel):
    type: Optional[str] = None
    service_name: str


class SafeEnvConfig(BaseModel):
    keyring: Optional[LocalKeyringSettings]
    env_nested_delimiter: Optional[str] = "."


class VaultConfigNoName(BaseModel):
    type: Optional[str] = "AzureKeyVault"
    params: Optional[Dict[str, str]] = None


class VaultConfig(VaultConfigNoName):
    name: str


class SecretConfigNoName(BaseModel):
    vault: Optional[str]
    vault_name: Optional[str]
    keyring_service_name: Optional[str]
    keyring_name: Optional[str]
    local: Optional[bool] = False


class SecretConfig(SecretConfigNoName):
    name: str


class ResourceTemplateConfigNoName(BaseModel):
    params: Optional[Dict[str, Optional[str]]] = None
    type: Optional[str] = "AzureREST"
    inputs: Optional[Dict[str, str]] = None


class ResourceTemplateConfig(ResourceTemplateConfigNoName):
    name: str


class ResourceConfigNoName(BaseModel):
    template: Optional[str]
    params: Optional[Dict[str, str]] = None
    cache_secret: Optional[str]
    query: Optional[str]
    parent: Optional[str]


class ResourceConfig(ResourceConfigNoName):
    name: str


class EnvironmentConfigurationMinimal(BaseModel):
    depends_on: Optional[List[str]] = None


class EnvironmentConfiguration(EnvironmentConfigurationMinimal):
    config: Optional[SafeEnvConfig]
    vaults: Optional[Dict[str,VaultConfigNoName]] = dict()
    secrets: Optional[Dict[str,SecretConfigNoName]] = dict()
    resources: Optional[Dict[str,ResourceConfigNoName]] = dict()
    parameters: Optional[Dict[str,str]] = dict()
    env: Optional[Dict[str,str]] = dict()
