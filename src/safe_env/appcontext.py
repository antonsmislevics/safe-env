from pathlib import Path
from typing import List
from .envmanager import EnvironmentManager
from .models import EnvironmentConfiguration


class AppContext():
    def __init__(self, config_dir: Path = None, verbose: bool = False):
        if not(config_dir):
            config_dir = Path("envs")
            
        self.config_dir = config_dir
        self.verbose = verbose
        self._load_env_man()        


    def _load_env_man(self):
        self.envman = EnvironmentManager()
        self.envman.load_from_folder(self.config_dir)
        

    def list_envs(self):
        return self.envman.list()


    def get_env(self, names: List[str]) -> EnvironmentConfiguration:
        return self.envman.load(names)
