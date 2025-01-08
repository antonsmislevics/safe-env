from pathlib import Path
from pydantic import BaseModel


class EnvironmentInfo(BaseModel):
    path: Path
    name: str
