from typing import Optional, List
from pathlib import Path
import typer
from .appcontext import AppContext
from . import utils

from . import __app_name__, __version__

app = typer.Typer()
secrets_app = typer.Typer()
app.add_typer(secrets_app, name="secrets")

ctx = None  # type: AppContext

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    verbose: bool = False,
    config_dir: Optional[Path] = None,
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


@app.command("list")
def list_envs():
    table = utils.print_table(
        ctx.envman.list(),
        fields=["name", "path"],
        headers=["Name", "Path"],
        sort_by_field_index=0
    )
    typer.echo(table)


@app.command("show")
def show_env(names: List[str]):
    obj = ctx.envman.load(names)
    obj_yaml = utils.print_yaml(obj)
    typer.echo(obj_yaml)


def get_env_vars_script(names: List[str], force_reload_from_remote: bool=False, is_bash: bool=False, is_powershell: bool=False, is_cmd: bool=False, is_docker_env: bool=False, is_unset: bool=False):
    obj = ctx.envman.load(names)
    env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = ctx.envman.get_env_variables_and_secrets(obj, force_reload_from_remote)
    if is_bash:
        script = utils.print_env_export_script_bash(env_variables, unset=is_unset)
    elif is_powershell:
        script = utils.print_env_export_script_powershell(env_variables, unset=is_unset)
    elif is_cmd:
        script = utils.print_env_export_script_cmd(env_variables, unset=is_unset)
    elif is_docker_env:
        script = utils.print_docker_env_content(env_variables, unset=is_unset)
    else:
        script = utils.print_yaml(env_variables, unset=is_unset)
    return script

@app.command("load")
def load_env(names: List[str], 
    force_reload_from_remote: Optional[bool] = typer.Option(
       None,
        "--force-reload-from-remote",
        "-f",
        help="Reload values cached in keyring from global keyvaults."
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
    is_docker_env: Optional[bool] = typer.Option(
        None,
            "--docker",
            help="Generate env file for docker-compose."
        )

    ):
    script = get_env_vars_script(names, force_reload_from_remote, is_bash, is_powershell, is_cmd, is_docker_env, is_unset=False)
    typer.echo(script)

# TODO: unload from env variable (without names parameter)
@app.command("unload")
def unload_env(names: List[str], 
    force_reload_from_remote: Optional[bool] = typer.Option(
       None,
        "--force-reload-from-remote",
        "-f",
        help="Reload values cached in keyring from global keyvaults."
    ),
    is_bash: Optional[bool] = typer.Option(
        None,
            "--bash",
            help="Generate bash env variable export script."
        ),
    is_powershell: Optional[bool] = typer.Option(
        None,
            "--ps2",
            "--ps",
            help="Generate PowerShell env variable export script."
        ),
    is_cmd: Optional[bool] = typer.Option(
        None,
            "--cmd",
            help="Generate CMD env variable export script."
        ),
    ):
    script = get_env_vars_script(names, force_reload_from_remote, is_bash, is_powershell, is_cmd, is_unset=True)
    typer.echo(script)


@secrets_app.command("list")
def list_secrets(names: List[str]):
    obj = ctx.envman.load(names)
    env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = ctx.envman.get_env_variables_and_secrets(obj, force_reload_from_remote=True)
    typer.echo("Remote secrets: ")
    typer.echo(utils.print_yaml(remote_secrets))
    typer.echo("Local only secrets:")
    typer.echo(utils.print_yaml(local_only_secrets))
    typer.echo("Remote cached secrets:")
    typer.echo(utils.print_yaml(remote_cached_secrets))


@secrets_app.command("clear")
def clear_cached_secrets(names: List[str]):
    # obj = man.get_env(names)
    # env_variables, remote_secrets, local_only_secrets, remote_cached_secrets = man.envman.get_env_variables_and_secrets(obj, force_reload_from_remote=True)
    # TODO: implement deleting of secrets
    typer.echo("Not implemented yet")    


if __name__ == "__main__":
    app()