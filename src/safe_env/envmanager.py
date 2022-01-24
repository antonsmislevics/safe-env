import os
from pathlib import Path
import logging
import yaml
from typing import Type, List, Dict
from pydantic import BaseModel, parse_obj_as
from safe_env.models.config import ResourceTemplateConfig, ResourceTemplateConfigNoName
from .models import EnvironmentConfiguration, EnvironmentConfigurationMinimal, EnvironmentInfo, ResourceTemplateConfig
from .envloader.envloader import EnvironmentLoader


class EnvironmentManager():
    def __init__(self):
        self.reload()


    def reload(self):
        self.env_info_list = []
        self.resource_template_list = []    # type: List[ResourceTemplateConfig]


    def load_from_folder(self, config_dir: Path):
        if not(config_dir.exists()):
            raise Exception(f"Config directory '{config_dir}' cannot be found.")
        
        for f in config_dir.glob("*.yaml"):
            self.add(f)

    def load_resource_tempates_from_folder(self, path: Path):
        if not(path.exists()):
            logging.warn(f"Resource Templates directory '{path}' cannot be found. Resource templates will not be loaded.")
            return

        for f in path.glob("*.yaml"):
            self.add_resource_template(f)
   

    def add(self, path: Path):
        env = EnvironmentInfo(
            path=path,
            name = os.path.splitext(path.name)[0]
        )
        self.env_info_list.append(env)

    def add_resource_template(self, path: Path):
        resource_tempates = self._load_yaml(path, Dict[str, ResourceTemplateConfigNoName])
        for key, value in resource_tempates.items():
            self.resource_template_list.append(ResourceTemplateConfig(name=key, **value.dict()))
    

    def get_resource_template(self, name) -> ResourceTemplateConfig:
        resource_template = next((x for x in self.resource_template_list if x.name == name), None)
        if not(resource_template):
            raise Exception(f"Resource template '{name}' cannot be found.")
        return resource_template


    def list(self):
        return self.env_info_list


    def get(self, name: str) -> EnvironmentInfo:
        env_info = next((x for x in self.env_info_list if x.name == name), None)
        if not(env_info):
            raise Exception(f"Environment '{name}' cannot be found.")
        return env_info


    def _load_env_yaml(self, name: str, target_type: Type[BaseModel]):
        env_info = self.get(name)
        return self._load_yaml(env_info.path, target_type)


    def _load_yaml(self, file_path: str, target_type: Type[BaseModel]):
        parsed_yaml = None
        with open(file_path, 'r') as f:
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
            return parse_obj_as(target_type, parsed_yaml)


    def load(self, names: List[str]) -> EnvironmentConfiguration:
        chain = self.get_env_list_chain(names)
        env_dict = self.get_merged_dict(chain)
        return EnvironmentConfiguration.parse_obj(env_dict)


    def get_env_variables_and_secrets(self,
                                      config: EnvironmentConfiguration,
                                      force_reload_from_remote: bool = False,
                                      force_reload_secrets: bool = False,
                                      force_reload_resources: bool = False,
                                      do_not_cache_resources: bool = False,
                                      do_not_cache_secrets: bool = False) -> Dict[str,str]:
        loader = EnvironmentLoader(config,
                                   get_resource_template_delegate=self.get_resource_template,
                                   force_reload_from_remote=force_reload_from_remote,
                                   force_reload_secrets=force_reload_secrets,
                                   force_reload_resources=force_reload_resources,
                                   do_not_cache_resources=do_not_cache_resources,
                                   do_not_cache_secrets=do_not_cache_secrets)
        return loader.load_envs_and_secrets()


    def get_env_chain(self, name: str, current_chain: List[str] = None) -> List[str]:
        chain = [] if current_chain is None else current_chain
        if name not in chain:
            env = self._load_env_yaml(name, EnvironmentConfigurationMinimal)    # type: EnvironmentConfigurationMinimal
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
            d = self._load_env_yaml(name, None)
            if d is None:
                continue
            if merged_dict is None:
                merged_dict = d
            else:
                self._merge_dict(merged_dict, d)
        if merged_dict is None:
            merged_dict = {}
        return merged_dict
