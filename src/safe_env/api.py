import os
from pathlib import Path
from typing import List, Union
from .appcontext import AppContext


def activate(
        names: Union[str, List[str]],
        config_dir: Union[str, Path] = None,
        verbose: bool = False,
        disable_plugins: bool = False,
        disable_unregistered_callables: bool = False,
        load_known_callables_from_modules: List[str] = None,
        force_reload: bool = False,
        no_cache: bool = False,
        flush_caches: bool = False
    ):
    if isinstance(config_dir, str):
        config_dir = Path(config_dir)
    
    if isinstance(names, str):
        names = [x.strip() for x in names.split(" ")]
        names = list([x for x in names if x])

    app_context = AppContext(
        config_dir=config_dir,
        verbose=verbose,
        disable_plugins=disable_plugins,
        disable_unregistered_callables=disable_unregistered_callables,
        load_known_callables_from_modules=load_known_callables_from_modules
    )
    app_context.load()
    envman = app_context.envman
    config = envman.load(names)
    config = envman.resolve(config,
                            force_reload=force_reload,
                            no_cache=no_cache,
                            flush_caches=flush_caches)
    env_variables = envman.get_env_variables(config)
    os.environ.update(env_variables)
