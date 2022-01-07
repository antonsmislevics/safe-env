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


class VaultConfig(BaseModel):
    name: str
    type: Optional[str] = "AzureKeyVault"
    params: Optional[Dict[str, str]] = None


class SecretConfig(BaseModel):
    name: str
    vault: Optional[str]
    vault_name: Optional[str]
    keyring_service_name: Optional[str]
    keyring_name: Optional[str]
    local: Optional[bool] = False


class ResourceConfig(BaseModel):
    name: str
    type: Optional[str] = "AzureREST"
    params: Optional[Dict[str, str]] = None
    query: Optional[str]
    cache_secret: Optional[str]


class EnvironmentConfigurationMinimal(BaseModel):
    depends_on: Optional[List[str]] = None


class EnvironmentConfiguration(EnvironmentConfigurationMinimal):
    config: Optional[SafeEnvConfig]
    vaults: Optional[List[VaultConfig]] = []
    secrets: Optional[List[SecretConfig]] = []
    resources: Optional[List[ResourceConfig]] = []
    parameters: Optional[Dict[str,str]] = dict()
    env: Optional[Dict[str,str]] = dict()
