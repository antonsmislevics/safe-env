import os
from pathlib import Path
import yaml
from typing import Type, List, Dict
from pydantic import BaseModel
from .models import EnvironmentConfiguration, EnvironmentConfigurationMinimal, EnvironmentInfo
from .envloader.envloader import EnvironmentLoader

class EnvironmentManager():
    def __init__(self):
        self.reload()


    def reload(self):
        self.env_info_list = []


    def load_from_folder(self, config_dir: Path):
        if not(config_dir.exists()):
            raise Exception(f"Config directory '{config_dir}' cannot be found.")
        
        for f in config_dir.glob("*.yaml"):
            self.add(f)


    def add(self, path: Path):
        env = EnvironmentInfo(
            path=path,
            name = os.path.splitext(path.name)[0]
        )
        self.env_info_list.append(env)


    def list(self):
        return self.env_info_list


    def get(self, name: str) -> EnvironmentInfo:
        env_info = next((x for x in self.env_info_list if x.name == name), None)
        if not(env_info):
            raise Exception(f"Environment '{name}' cannot be found.")
        return env_info


    def _load_yaml(self, name: str, target_type: Type[BaseModel]):
        parsed_yaml = None
        env_info = self.get(name)
        with open(env_info.path, 'r') as f:
            try:
                parsed_yaml=yaml.safe_load(f)
                if parsed_yaml is None:
                    parsed_yaml = {}
            except yaml.YAMLError as exc:
                raise
        if parsed_yaml is None:
            return None
        elif target_type is None:
            return parsed_yaml
        else:
            return target_type.parse_obj(parsed_yaml)


    def load(self, names: List[str]) -> EnvironmentConfiguration:
        chain = self.get_env_list_chain(names)
        env_dict = self.get_merged_dict(chain)
        return EnvironmentConfiguration.parse_obj(env_dict)


    def get_env_variables_and_secrets(self, config: EnvironmentConfiguration, force_reload_from_remote: bool = False) -> Dict[str,str]:
        loader = EnvironmentLoader(config, force_reload_from_remote)
        return loader.load_envs_and_secrets()


    def get_env_chain(self, name: str, current_chain: List[str] = None) -> List[str]:
        chain = [] if current_chain is None else current_chain
        if name not in chain:
            env = self._load_yaml(name, EnvironmentConfigurationMinimal)    # type: EnvironmentConfigurationMinimal
            if env.depends_on:
                for dep_name in env.depends_on:
                    chain = self.get_env_chain(dep_name, chain)
            chain.append(name)
        return chain


    def get_env_list_chain(self, names: List[str]):
        chain = []
        for name in names:
            chain = self.get_env_chain(name, chain)
        return chain


    def _merge_dict(self, d1, d2):
        for k in d2:
            if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
                self._merge_dict(d1[k], d2[k])
            else:
                d1[k] = d2[k]


    def get_merged_dict(self, names: List[str]):
        merged_dict = None
        for name in names:
            d = self._load_yaml(name, None)
            if d is None:
                continue
            if merged_dict is None:
                merged_dict = d
            else:
                self._merge_dict(merged_dict, d)
        if merged_dict is None:
            merged_dict = {}
        return merged_dict
