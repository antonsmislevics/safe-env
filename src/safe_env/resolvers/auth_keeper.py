from typing import Dict, Any
from keepercommander import api
from keepercommander.api import KeeperParams


def get_keeper_login_params(
    username: str = None,
    keeper_params_kwargs: Dict[str, Any] = None 
) -> KeeperParams:
    if keeper_params_kwargs is None:
        keeper_params_kwargs = dict()

    login_params = KeeperParams(**keeper_params_kwargs)
    if username is None:
        username = input('Please enter Keeper User (Email): ')
    login_params.user = username
    api.login(login_params)
    api.sync_down(login_params)
    return login_params
