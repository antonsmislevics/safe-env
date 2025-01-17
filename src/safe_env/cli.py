import subprocess
import os
import sys
import shlex
import runpy
from typing import Optional, List, Annotated
from pathlib import Path
import fsspec
from fsspec.utils import infer_storage_options
import typer
import json
import glob
from tqdm import tqdm

from .appcontext import AppContext
from . import utils

from . import __app_name__, __version__

app = typer.Typer()

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    verbose: bool = False,
    config_dir: Optional[Path] = typer.Option(
       "./envs",
        "--config-dir",
        "-c",
        help="Path to the directory where environment configuration files are stored.",
        envvar="SAFE_ENV_CONFIG_DIR"
    ),
    disable_plugins: Optional[bool] = typer.Option(
        False,
        "--disable-plugins",
        help="Disable loading plugins.",
        envvar="SAFE_ENV_DISABLE_PLUGINS"
    ),
    disable_unregistered_callables: Optional[bool] = typer.Option(
        False,
        "--disable-unregistered-callables",
        help="Allow using only registered callables by their short names.",
        envvar="SAFE_ENV_DISABLE_UNREGISTERED_CALLABLES"
    ),
    register_modules: Optional[str] = typer.Option(
        None,
        "--register-modules",
        help="Comma separated list of module names, from which short names for callables should be loaded.",
        envvar="SAFE_ENV_REGISTER_MODULES"
    ),
    version: Optional[bool] = typer.Option(
       None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True
    )
) -> None:
    load_known_callables_from_modules = []
    if register_modules is not None:
        load_known_callables_from_modules += [x.strip() for x in register_modules.split(",")]

    ctx = AppContext(config_dir, verbose, disable_plugins, disable_unregistered_callables, load_known_callables_from_modules)
    ctx.set_as_global_context()
    return

@app.command("list", help="List available environments.")
def list_envs():
    AppContext.GLOBAL_APP_CONTEXT.load()
    table = utils.print_table(
        AppContext.GLOBAL_APP_CONTEXT.envman.list(),
        fields=["name", "path"],
        headers=["Name", "Path"],
        sort_by_field_index=0
    )
    typer.echo(table)
    # typer.echo("Not implemented yet")    


def _process_config(names: List[str], resolve: bool = False, get_envs: bool = False, **kwargs):
    AppContext.GLOBAL_APP_CONTEXT.load()
    envman = AppContext.GLOBAL_APP_CONTEXT.envman
    config = envman.load(names)

    if resolve:
        config = envman.resolve(config, **kwargs)

        if get_envs:
            config = envman.get_env_variables(config)

    return envman, config

@app.command("show", help="Show aggregated configuration YAML file for specified environments.")
def show_env(names: Annotated[List[str], typer.Argument(envvar="SAFE_ENV_NAMES", help="Environment names.")]):
    envman, config = _process_config(names, resolve=False, get_envs=False)
    config_yaml = envman.raw_config_to_yaml(config)
    typer.echo(config_yaml)

@app.command("resolve", help="Resolve aggregated configuration YAML file for specified environments.")
def resolve_env(names: Annotated[List[str], typer.Argument(envvar="SAFE_ENV_NAMES", help="Environment names.")],
                force_reload: Optional[bool] = typer.Option(
                        False,
                        "--force-reload",
                        "-f",
                        help="Ignore all cached values and reload from sources."
                    ),
                no_cache: Optional[bool] = typer.Option(
                        False,
                        "--no-cache",
                        "-n",
                        help="Do use caches to load/save values."
                    )
                ):
    envman, config = _process_config(names,
                                     resolve=True,
                                     get_envs=False, force_reload=force_reload,
                                     no_cache=no_cache)
    config_yaml = envman.resolved_config_to_yaml(config)
    typer.echo(config_yaml)

@app.command("flush", help="Delete values stored in all caches for specified environments. Environments will need to be resolved during the process.")
def flush_env(names: Annotated[List[str], typer.Argument(envvar="SAFE_ENV_NAMES", help="Environment names.")]):
    envman, config = _process_config(names,
                                     resolve=True,
                                     get_envs=False,
                                     flush_caches=True)
    typer.echo("Flushing caches completed.")


def get_env_vars_script(names: List[str],
                        force_reload: bool=False,
                        no_cache: bool=False,
                        is_bash: bool=False,
                        is_powershell: bool=False,
                        is_cmd: bool=False,
                        is_env: bool=False,
                        is_docker_env: bool=False,
                        is_unset: bool=False):
    _, env_variables = _process_config(names,
                                       resolve=True,
                                       get_envs=True,
                                       force_reload=force_reload,
                                       no_cache=no_cache)
    if is_bash:
        script = utils.print_env_export_script_bash(env_variables, unset=is_unset)
    elif is_powershell:
        script = utils.print_env_export_script_powershell(env_variables, unset=is_unset)
    elif is_cmd:
        script = utils.print_env_export_script_cmd(env_variables, unset=is_unset)
    elif is_env:
        script = utils.print_env_content(env_variables, unset=is_unset)
    elif is_docker_env:
        script = utils.print_docker_env_content(env_variables, unset=is_unset)
    else:
        script = utils.print_yaml(env_variables, unset=is_unset)
    return script

@app.command("activate", help="Activate specified environments. Without other parameters the command will only show what environment variables will be set after activation. Use additional parameters to generate env variable export script for specific platform (run \"se activate --help\" for more details).")
def load_env(names: Annotated[List[str], typer.Argument(envvar="SAFE_ENV_NAMES", help="Environment names.")], 
    force_reload: Optional[bool] = typer.Option(
       False,
        "--force-reload",
        "-f",
        help="Ignore all cached values and reload from sources."
    ),
    no_cache: Optional[bool] = typer.Option(
       False,
        "--no-cache",
        "-n",
        help="Do not use caches to load/save values."
    ),
    is_bash: Optional[bool] = typer.Option(
        None,
            "--bash",
            help="Generate bash env variable export script."
        ),
    is_powershell: Optional[bool] = typer.Option(
        None,
            "--ps",
            "--powershell",
            help="Generate PowerShell env variable export script."
        ),
    is_cmd: Optional[bool] = typer.Option(
        None,
            "--cmd",
            help="Generate CMD env variable export script."
        ),
    is_env: Optional[bool] = typer.Option(
        None,
            "--env",
            help="Generate env file."
        ),
    is_docker_env: Optional[bool] = typer.Option(
        None,
            "--docker",
            help="Generate env file for docker-compose."
        ),
    out_path: Optional[str] = typer.Option(
        None,
            "--out",
            help="Path of the file where to save output."
        )
    ):
    if (out_path is None) and (is_bash or is_cmd or is_env or is_docker_env or is_powershell):
        # disable printing logs since script code is written to console
        AppContext.GLOBAL_APP_CONTEXT.switch_output_to_command_mode()
    
    script = get_env_vars_script(names,
                                force_reload,
                                no_cache,
                                is_bash,
                                is_powershell,
                                is_cmd,
                                is_env,
                                is_docker_env,
                                is_unset=False)
    if out_path is None:
        typer.echo(script)
    else:
        with open(out_path, 'w', encoding="utf-8") as f:
            f.write(script)

@app.command("run", help="Run command (sub process) or python module with specified environments activated.")
def run_in_env(names: Annotated[List[str], typer.Argument(envvar="SAFE_ENV_NAMES", help="Environment names.")],
        cmd: str = typer.Option(
            ...,
            "--cmd",
            "-c",
            help="Command to run.",
        ),
        run_as_python_module: Optional[bool] = typer.Option(
            False,
            "--python-module",
            "-py",
            help="Run command as python module (does not create separate process)."
        ),
        no_host_env_variables: Optional[bool] = typer.Option(
            False,
            "--no-host-envs",
            help="Do not pass env variables from host (current terminal session)."
        ),
        force_reload: Optional[bool] = typer.Option(
            False,
            "--force-reload",
            "-f",
            help="Ignore all cached values and reload from sources."
        ),
        no_cache: Optional[bool] = typer.Option(
            False,
            "--no-cache",
            "-n",
            help="Do not use caches to load/save values."
        )
    ):
    _, env_variables = _process_config(names,
                                       resolve=True,
                                       get_envs=True,
                                       force_reload=force_reload,
                                       no_cache=no_cache)

    cmd_args = shlex.split(cmd)
    if no_host_env_variables:
        os.environ.clear()
    os.environ.update(env_variables)
    if run_as_python_module:
        sys.argv = cmd_args
        module_name = cmd_args[0]
        runpy.run_module(module_name, run_name="__main__")
    else:
        subprocess.run(cmd_args, env=os.environ)

@app.command("push", help="Push environment configurations to specified location.")
def push_envs(names: Annotated[Optional[List[str]], typer.Argument()] = None,
        push_all: Optional[bool] = typer.Option(
            False,
            "--all",
            help="Push all environments."
        ),
        overwrite: Optional[bool] = typer.Option(
            False,
            "--overwrite",
            help="Overwrite files at destination."
        ),
        no_dependencies: Optional[bool] = typer.Option(
            False,
            "--no-deps",
            help="Push only specified environments, without environments they depend on."
        ),
        no_plugins: Optional[bool] = typer.Option(
            False,
            "--no-plugins",
            help="Do not push plugins."
        ),
        url: str = typer.Option(
            ...,
            "--url",
            help="Remote location where environment configurations should be uploaded (fsspec format)."
        ),
        storage_options_json: str = typer.Option(
            None,
            "--storage-options",
            help="fsspec provider storage options for remote location (JSON string)."
        )
    ):
        if (names is None) and not(push_all):
            typer.echo("Error: environment names or --all must be specified.")
            return

        AppContext.GLOBAL_APP_CONTEXT.load()
        envman = AppContext.GLOBAL_APP_CONTEXT.envman

        if push_all:
            env_names = list([x.name for x in envman.list()])
        else:
            if no_dependencies:
                # try getting environments by name to validate that environments exist
                env_names = list([envman.get(x).name for x in names])
            else:
                env_names = envman.get_env_list_chain(names, skip_dependency_loops=True)

        config_dir = AppContext.GLOBAL_APP_CONTEXT.config_dir
        plugins_dir = AppContext.GLOBAL_APP_CONTEXT.plugins_dir

        storage_options = infer_storage_options(url)

        source_path = config_dir
        target_path = storage_options.get("host", "") + storage_options.get("path")


        if storage_options_json is not None:
            storage_options.update(
                json.loads(storage_options_json)
            )

        fs = fsspec.filesystem(**storage_options)

        files_to_upload = [
            envman.get_filename_from_env_name(env_name) for env_name in env_names
        ]

        if not(no_plugins):
            # collect python files for plugins plugins
            py_files_pattern = os.path.join(plugins_dir, '**/*.py')
            files_to_upload += [
                os.path.relpath(file_path, source_path) 
                    for file_path in glob.glob(py_files_pattern, recursive=True)
            ]

        for file_name in tqdm(files_to_upload, desc="Uploading"):
            source_file_path = os.path.join(source_path, file_name)
            target_file_path = os.path.join(target_path, file_name)
            fs.put(source_file_path, target_file_path, overwrite=overwrite, **storage_options)

@app.command("pull", help="Pull environment configurations from specified location.")
def pull_envs(
        overwrite: Optional[bool] = typer.Option(
            False,
            "--overwrite",
            help="Overwrite files at destination."
        ),
        url: str = typer.Option(
            ...,
            "--url",
            help="Remote location from where environment configurations should be downloaded (fsspec format).",
            envvar="SAFE_ENV_CONFIG_REMOTE_URL"
        ),
        storage_options_json: str = typer.Option(
            None,
            "--storage-options",
            help="fsspec provider storage options for remote location (JSON string).",
            envvar="SAFE_ENV_CONFIG_REMOTE_OPTIONS"
        )
    ):

    storage_options = infer_storage_options(url)
    remote_path = storage_options.get("host", "") + storage_options.get("path")
    local_path = AppContext.GLOBAL_APP_CONTEXT.config_dir
    local_path = str(local_path).rstrip("\\/")

    if storage_options_json is not None:
        storage_options.update(
            json.loads(storage_options_json)
        )

    fs = fsspec.filesystem(**storage_options)
    fs.get(remote_path, local_path, recursive=True, overwrite=overwrite)

if __name__ == "__main__":
    app()
