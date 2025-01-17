from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AzureKeyVaultCertificate(BaseModel):
    name: str
    thumbprint: str
    private_key: Optional[str]

class AzureKeyVaultKeyProperties(BaseModel):
    content_type: Optional[str]
    created_on: Optional[datetime]
    enabled: Optional[bool]
    expires_on: Optional[datetime]
    id: Optional[str]
    key_id: Optional[str]
    managed: Optional[bool]
    name: Optional[str]
    not_before: Optional[datetime]
    recoverable_days: Optional[int]
    recovery_level: Optional[str]
    tags: Optional[Dict[str,Any]]
    updated_on: Optional[datetime]
    vault_url: Optional[str]
    version: Optional[str]

class AzureKeyVaultKey(BaseModel):
    id: Optional[str]
    name: Optional[str]
    value: Optional[str]
    properties: Optional[AzureKeyVaultKeyProperties]
