from typing import Optional, List
from pathlib import Path
import typer
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
        help="Path to the directory where environment configuration files are stored."
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
    ctx = AppContext(config_dir, verbose)
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
def show_env(names: List[str]):
    envman, config = _process_config(names, resolve=False, get_envs=False)
    config_yaml = envman.raw_config_to_yaml(config)
    typer.echo(config_yaml)

@app.command("resolve", help="Resolve aggregated configuration YAML file for specified environments.")
def resolve_env(names: List[str],
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
def flush_env(names: List[str]):
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
def load_env(names: List[str], 
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

if __name__ == "__main__":
    app()
