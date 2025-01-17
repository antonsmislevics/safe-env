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
    def __init__(self,
                 disable_plugins: bool = False,
                 disable_unregistered_callables: bool = False,
                 load_known_callables_from_modules: List[str] = None):
        self.plugins_module_name = "_plugins_"
        self.resolver_manager = None
        self.disable_plugins = disable_plugins
        self.disable_unregistered_callables = disable_unregistered_callables
        self.load_known_callables_from_modules = load_known_callables_from_modules
        self.reload()

    def reload(self):
        self.env_info_list = []
        self.plugins_module = None
        self.resolver_manager = None

    def load_from_folder(self, config_dir: Path):
        if not(config_dir.exists()):
            raise Exception(f"Config directory '{config_dir}' cannot be found.")
        
        for f in config_dir.glob("**/*.yaml"):
            self.add(f, config_dir)

    def load_plugins(self, plugins_dir: Path):
        if self.disable_plugins:
            logging.info("Plugins are disabled. Skip loading plugins.")
            return

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
            flush_caches,
            self.disable_unregistered_callables,
            self.load_known_callables_from_modules
        )
        self.resolver_manager.register_resolvers()

    def _normalize_env_or_dependency_name(self, name: str):
        # ensure that env and dependency names have consistent "/" on windows and linux
        return name.replace("\\", "/")

    def add(self, path: Path, config_dir: Path):
        env_file_name = os.path.relpath(path, config_dir)
        env_name = os.path.splitext(env_file_name)[0]
        env_name = self._normalize_env_or_dependency_name(env_name)

        env = EnvironmentInfo(
            path=path,
            name = env_name
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

    def get_filename_from_env_name(self, env_name: str):
        return f"{env_name}.yaml"

    def get_target_env_name_from_dependency(self, env_name: str, dep_name: str):
        dep_name = self._normalize_env_or_dependency_name(dep_name)
        if dep_name.startswith("/"):
            # treat as dependency name starting from root of config folder
            return dep_name[1:]
        else:
            # resolves relative dependency names with ".." or subfolder names
            env_dir_name = os.path.dirname(env_name)
            target_env_name = os.path.join(env_dir_name, dep_name)
            # remove ".." to get proper env_name
            target_env_name = os.path.normpath(target_env_name)
            target_env_name = self._normalize_env_or_dependency_name(target_env_name)
            return target_env_name

    def get_env_chain(self, name: str, current_chain: List[str] = None, skip_dependency_loops: bool = False) -> List[str]:
        chain = [] if current_chain is None else current_chain
        if name in chain:
            if skip_dependency_loops:
                return chain
            else:
                raise Exception(f"Potential dependency loop detected. Environment name is already in dependency chain: '{name}'.")
        # to catch potential dependency loops with self, add name to the chain first
        chain.append(name)
        env = self._load_env_yaml(name, EnvironmentConfigurationMinimal)    # type: EnvironmentConfigurationMinimal
        if env.depends_on:
            # start with the last dependency (top layer)
            for dep_name in reversed(env.depends_on):
                target_env_name = self.get_target_env_name_from_dependency(name, dep_name)
                chain = self.get_env_chain(target_env_name, chain, skip_dependency_loops)
        return chain

    def get_env_list_chain(self, names: List[str], skip_dependency_loops: bool = False):
        chain = []
        # start from last envrionment (the one that should be on top)
        for name in reversed(names):
            chain = self.get_env_chain(name, chain, skip_dependency_loops)
        # reverse the list so environments are in the sequence, in which they need to be applied
        chain = list(reversed(chain))
        return chain

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
