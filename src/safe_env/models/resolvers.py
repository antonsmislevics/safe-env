from typing import Optional, List, Dict, Any, Callable, Union
from pydantic import BaseModel

class MethodParams(BaseModel):
    args: Optional[List[Any]] = list()
    kwargs: Optional[Dict[str, Any]] = dict()

class CallResolverParamsBase(BaseModel):
    init_params: Optional[MethodParams] = MethodParams()
    method: Optional[str] = None
    args: Optional[List[Any]] = list()
    kwargs: Optional[Dict[str, Any]] = dict()

class CacheProviderParams(CallResolverParamsBase):
    name: str
    provider: Union[str, Callable]
    required: Optional[bool] = False
    get_method: Optional[str] = "get"
    set_method: Optional[str] = "set"
    delete_method: Optional[str] = "delete"
    get_params: Optional[MethodParams] = None
    set_params: Optional[MethodParams] = None
    delete_params: Optional[MethodParams] = None

class CallResolverParams(CallResolverParamsBase):
    selector: Optional[str] = None
    as_container: Optional[bool] = False
    cache: Optional[Dict[str, CacheProviderParams]] = dict()
