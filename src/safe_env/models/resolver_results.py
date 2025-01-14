from typing import Optional
from pydantic import BaseModel

class AzureKeyVaultCertificate(BaseModel):
    name: str
    thumbprint: str
    private_key: Optional[str]
