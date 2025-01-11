# Getting started
In this section we cover how to install **safe-env**, and check that the installation was successful.
## How to install?
The package can be installed using pip:
```bash
python -m pip install safe-env
```

If using uv, it can be installed globally as a tool or as a dev dependency in specific project:
```bash
# install as a tool
uv tool safe-env

# or add as dev dependency
uv add safe-env --dev
```

Latest dev version can also be installed directly from git repository:
```bash
# pip
python -m pip install git+https://github.com/antonsmislevics/safe-env.git

# uv as a tool
uv tool install git+https://github.com/antonsmislevics/safe-env.git

# uv as dev dependency
uv add git+https://github.com/antonsmislevics/safe-env.git --dev
```

The package does not require to be installed in the same virtual environment that is used for development.

## How to use?

When the package is installed, **safe-env** can be invoked from the command line as `se` or as `python -m safe_env`.

To check the version of the tool, run:
```bash
se --version

# or

python -m safe_env --version
```

To get a list of all available commands and options, run:
```bash
se --help

# or

python -m safe_env --help
```
<b>Congratulations!</b> Now you are ready to [create environment configuration files](working-with-envs.md).
