from typing import Optional, List
from pathlib import Path
import typer
from .appcontext import AppContext
from . import utils

from . import __app_name__, __version__

app = typer.Typer()
secrets_app = typer.Typer()
app.add_typer(secrets_app, name="secrets", help="Work with secrets for specified environments.")

ctx = None  # type: AppContext

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
    global ctx
    ctx = AppContext(config_dir, verbose)
    return


@app.command("list", help="List available environments.")
def list_envs():
    ctx.load()
    table = utils.print_table(
        ctx.envman.list(),
        fields=["name", "path"],
        headers=["Name", "Path"],
        sort_by_field_index=0
    )
    typer.echo(table)


@app.command("show", help="Show aggregated configuration YAML file for specified environments.")
def show_env(names: List[str]):
    ctx.load()
    obj = ctx.envman.load(names)
    obj_yaml = utils.print_yaml(obj)
    typer.echo(obj_yaml)


def get_env_vars_script(names: List[str],
                        force_reload_from_remote: bool=False,
                        is_bash: bool=False,
                        is_powershell: bool=False,
                        is_cmd: bool=False,
                        is_env: bool=False,
                        is_docker_env: bool=False,
                        is_unset: bool=False,
                        force_reload_secrets: bool = False,
                        force_reload_resources: bool = False,
                        do_not_cache_resources: bool = False,
                        do_not_cache_secrets: bool = False):
    obj = ctx.envman.load(names)
    env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = ctx.envman.get_env_variables_and_secrets(obj,
                                                                                                                        force_reload_from_remote=force_reload_from_remote,
                                                                                                                        force_reload_secrets=force_reload_secrets,
                                                                                                                        force_reload_resources=force_reload_resources,
                                                                                                                        do_not_cache_resources=do_not_cache_resources,
                                                                                                                        do_not_cache_secrets=do_not_cache_secrets)
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
    force_reload_from_remote: Optional[bool] = typer.Option(
       None,
        "--force-reload-from-remote",
        "-f",
        help="Reload values cached in keyring from global keyvaults and resources."
    ),
    force_reload_secrets: Optional[bool] = typer.Option(
       None,
        "--force-reload-secrets",
        "-fs",
        help="Reload values cached in keyring from global keyvaults."
    ),
    force_reload_resources: Optional[bool] = typer.Option(
       None,
        "--force-reload-resources",
        "-fr",
        help="Reload values cached in keyring and global keyvaults from resources."
    ),
    do_not_cache_resources: Optional[bool] = typer.Option(
       None,
        "--no-cache-resources",
        "-ncr",
        help="Do not save values loaded from resources in keyring and global keyvaults."
    ),
    do_not_cache_secrets: Optional[bool] = typer.Option(
       None,
        "--no-cache-secrets",
        "-ncs",
        help="Do not save secrets from global keyvaults in local keyring."
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
        ctx.switch_output_to_command_mode()
    
    ctx.load()
    
    script = get_env_vars_script(names,
                                force_reload_from_remote,
                                is_bash,
                                is_powershell,
                                is_cmd,
                                is_env,
                                is_docker_env,
                                is_unset=False,
                                force_reload_secrets=force_reload_secrets,
                                force_reload_resources=force_reload_resources,
                                do_not_cache_resources=do_not_cache_resources,
                                do_not_cache_secrets=do_not_cache_secrets)
    if out_path is None:
        typer.echo(script)
    else:
        with open(out_path, 'w') as f:
            f.write(script)


@secrets_app.command("list", help="List secrets configuration for specified environments.")
def list_secrets(names: List[str]):
    ctx.load()
    obj = ctx.envman.load(names)
    env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = ctx.envman.get_env_variables_and_secrets(obj, force_reload_from_remote=True)
    typer.echo("Remote secrets: ")
    typer.echo(utils.print_yaml(remote_secrets))
    typer.echo("Local only secrets:")
    typer.echo(utils.print_yaml(local_only_secrets))
    typer.echo("Remote cached secrets:")
    typer.echo(utils.print_yaml(remote_cached_secrets))


@secrets_app.command("clear", help="Delete activated/cached secrets for specified environments.")
def clear_cached_secrets(names: List[str]):
    ctx.load()
    # obj = man.get_env(names)
    # env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = man.envman.get_env_variables_and_secrets(obj, force_reload_from_remote=True)
    # TODO: implement deleting of secrets
    typer.echo("Not implemented yet")    


if __name__ == "__main__":
    app()
