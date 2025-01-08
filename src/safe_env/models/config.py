from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Callable


# Minimal set of environment configuration attributes needed for dependency resolution
# Note: this can be partial environment configuration that does not have envs block
class EnvironmentConfigurationMinimal(BaseModel):
    depends_on: Optional[List[str]] = None

# Minimal set of environment configuration attributes needed to prepare the list of resolved environment variables
class EnvironmentConfigurationFinal(BaseModel):
    envs: Optional[Dict[str, Any]] = dict()

# Resolver configuration model
class ResolverConfiguration(BaseModel):
    name: str
    func: Callable
    use_cache: Optional[bool] = False
