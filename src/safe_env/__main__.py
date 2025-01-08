from . import cli, __app_name__

def main():
    cli.app(prog_name=__app_name__)
    # cli.app()


if __name__ == "__main__":
    main()