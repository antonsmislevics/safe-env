# content of test_pyconv.py

import pytest

env_list = [
    "base",
    "dev",
    "dev1",
    "dev2",
    "dev local"
]

cmd_list = [
    "show",
    "resolve",
    "activate"
]

cmds = [
    "se list"
]
for cmd in cmd_list:
    for env in env_list:
        cmds += [f"se {cmd} {env}"]



@pytest.mark.parametrize("cmd", cmds)
def test_cmd(cmd, simple_env, run, get_expected_result, monkeypatch: pytest.MonkeyPatch):
    (working_dir, config_dir) = simple_env
    monkeypatch.chdir(working_dir)
    result = run(cmd)
    assert result.ret == 0
    assert str(result.stdout) == get_expected_result(cmd)

@pytest.mark.parametrize("cmd", cmds[1:])   # remove "se list" test since it is expected to fail
def test_cmd_with_config_dir(cmd, simple_env, run, get_expected_result):
    (working_dir, config_dir) = simple_env
    cmd_with_config_dir = f"se --config-dir {config_dir} {cmd[3:]}"
    result = run(cmd_with_config_dir)
    assert result.ret == 0
    assert str(result.stdout) == get_expected_result(cmd)
