import tests.resources
from importlib.resources import files
import pytest
import shutil

pytest_plugins = ["pytester"]

def copy_env_from_folder(tmpdir_factory, name: str):
    working_dir = tmpdir_factory.mktemp("t")
    config_dir = working_dir.join("envs")
    samples_base_path = files(tests.resources).joinpath(name)
    shutil.copytree(samples_base_path, config_dir)
    return (working_dir, config_dir)

@pytest.fixture
def get_expected_result():
    def do_get_expected_result(cmd: str):
        result_file = f"results/{cmd.replace(' ', '-')}.txt"
        expected_result_file = files(tests.resources).joinpath(result_file)
        expected_result = None
        if expected_result_file.is_file():
            expected_result = expected_result_file.read_text()
        return expected_result
    return do_get_expected_result

@pytest.fixture(scope="session")
def simple_env(tmpdir_factory):
    (working_dir, config_dir) = copy_env_from_folder(
        tmpdir_factory,
        "envs"
    )
    yield (working_dir, config_dir)


@pytest.fixture
def run(testdir):
    def do_run(cmd):
        args = [x for x in cmd.split(" ") if x != ""]
        return testdir.run(*args)
    return do_run