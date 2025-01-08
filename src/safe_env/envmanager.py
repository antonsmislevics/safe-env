import os
from pathlib import Path
import logging
import yaml
from typing import Type, List, Dict, Union
from pydantic import BaseModel, TypeAdapter

from importlib.machinery import SourceFileLoader
from omegaconf import OmegaConf, ListConfig, DictConfig

from .models import (
    EnvironmentInfo,
    EnvironmentConfigurationMinimal,
    EnvironmentConfigurationFinal
)

from . import utils
from . import resolvers


class EnvironmentManager():
    def __init__(self):
        self.plugins_module_name = "_plugins_"
        self.resolver_manager = None
        self.reload()

    def reload(self):
        self.env_info_list = []
        self.plugins_module = None
        self.resolver_manager = None


        # self.resource_template_list = []    # type: List[ResourceTemplateConfig]


    def load_from_folder(self, config_dir: Path):
        if not(config_dir.exists()):
            raise Exception(f"Config directory '{config_dir}' cannot be found.")
        
        for f in config_dir.glob("*.yaml"):
            self.add(f)

    def load_plugins(self, plugins_dir: Path):
        if not(plugins_dir.exists()):
            logging.info("Plugins folder does not exist. Skip loading plugins.")
            return
        
        init_file_path = plugins_dir.joinpath("__init__.py")
        if not(init_file_path.exists()):
            logging.error(f"Cannot load plugins, since there is no __init__.py file in plugins folder: {init_file_path}")
            return
        
        plugins_module = SourceFileLoader(self.plugins_module_name, str(init_file_path)).load_module()
        self.plugins_module = plugins_module

    def load_resolvers(self, force_reload: bool=False, no_cache: bool=False, flush_caches: bool=False):
        self.resolver_manager = resolvers.ResolverManager(
            self.plugins_module_name,
            self.plugins_module,
            force_reload,
            no_cache,
            flush_caches
        )
        self.resolver_manager.register_resolvers()

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


    def _load_env_yaml(self, name: str, target_type: Type[BaseModel]):
        env_info = self.get(name)
        return self._load_yaml(env_info.path, target_type)


    def _load_yaml(self, file_path: str, target_type: Type[BaseModel]):
        conf = None
        parsed_yaml = None
        try:
            # TODO check what exceptions are returned
            with open(file_path, 'r') as f:
                try:
                    parsed_yaml=yaml.safe_load(f)
                    if parsed_yaml is None:
                        parsed_yaml = {}
                except yaml.YAMLError:
                    raise
        except yaml.YAMLError:
            # TODO check how to handle yaml loading exception
            raise

        if parsed_yaml:
            # TODO check how to handle OmegaConf exceptions
            conf = OmegaConf.create(parsed_yaml, flags={"allow_objects": True})
        if conf is None:
            return None
        elif target_type is None:
            return conf
        else:
            ta = TypeAdapter(target_type)
            obj = ta.validate_python(conf)
            return obj

    def load(self, names: List[str]) -> Union[ListConfig, DictConfig]:
        chain = self.get_env_list_chain(names)
        merged_config = self.get_merged_config(chain)
        return merged_config

    def resolve(self,
                config: Union[ListConfig, DictConfig],
                force_reload: bool = False,
                no_cache: bool = False,
                flush_caches: bool = False) -> Union[ListConfig, DictConfig]:
        self.load_resolvers(force_reload, no_cache, flush_caches)
        OmegaConf.resolve(config)
        return config

    def raw_config_to_yaml(self, config: Union[ListConfig, DictConfig]) -> str:
        return OmegaConf.to_yaml(config)
    
    def resolved_config_to_yaml(self, config: Union[ListConfig, DictConfig]) -> str:
        return utils.print_yaml(OmegaConf.to_object(config))
    
    def get_env_variables(self, config: Union[ListConfig, DictConfig]) -> Dict[str, str]:
        if config is None:
            return dict()
        
        ta = TypeAdapter(EnvironmentConfigurationFinal)
        obj = ta.validate_python(config)

        # normalize output - convert all values to strings
        result = {name: str(value) for name, value in obj.envs.items()}
        return result

    # def get_env_variables_and_secrets(self,
    #                                   config: EnvironmentConfiguration,
    #                                   force_reload_from_remote: bool = False,
    #                                   force_reload_secrets: bool = False,
    #                                   force_reload_resources: bool = False,
    #                                   do_not_cache_resources: bool = False,
    #                                   do_not_cache_secrets: bool = False) -> Dict[str,str]:
    #     loader = EnvironmentLoader(config,
    #                                get_resource_template_delegate=self.get_resource_template,
    #                                force_reload_from_remote=force_reload_from_remote,
    #                                force_reload_secrets=force_reload_secrets,
    #                                force_reload_resources=force_reload_resources,
    #                                do_not_cache_resources=do_not_cache_resources,
    #                                do_not_cache_secrets=do_not_cache_secrets)
    #     return loader.load_envs_and_secrets()


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


    # def _merge_dict(self, d1, d2):
    #     for k in d2:
    #         if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
    #             self._merge_dict(d1[k], d2[k])
    #         else:
    #             d1[k] = d2[k]


    def get_merged_config(self, names: List[str]) -> Union[ListConfig, DictConfig]:
        configs_to_merge = []
        for name in names:
            config = self._load_env_yaml(name, None)
            configs_to_merge.append(config)
        merged_config = OmegaConf.merge(*configs_to_merge)
        
        # remove depends on attribute after merge, if exists
        if hasattr(merged_config, "depends_on"):
            del merged_config.depends_on

        return merged_config
