import json
import pytest
from git import Repo
from git.exc import GitCommandError
from pathlib import Path
from dbt_auto_defer import cli

REMOTE_FILES = {"a":"a different content here", "b": "b content here"}
REMOTE_BRANCH = "example-branch"

SAMPLE_CONFIG = {
    "branch": f"origin/{REMOTE_BRANCH}",
    "files": REMOTE_FILES,
    "out": "out-dir",
}


def _are_files_available(dbt_repo, *, should_be_available=True):
    if should_be_available:
        for file, content in REMOTE_FILES.items():
            assert dbt_repo.git.show(f"{SAMPLE_CONFIG['branch']}:{file}") == content
    else:
        with pytest.raises(GitCommandError):
            for file, content in REMOTE_FILES.items():
                assert dbt_repo.git.show(f"{SAMPLE_CONFIG['branch']}:{file}") == content


@pytest.fixture(scope="function")
def dbt_repo(tmp_path_factory) -> Repo:
    dbt_repo_path = tmp_path_factory.mktemp("dbt_repo")
    _dbt_repo = Repo.init(dbt_repo_path)

    dbt_repo_remote_path = tmp_path_factory.mktemp("dbt_repo_remote")

    remote = Repo.init(dbt_repo_remote_path, initial_branch=REMOTE_BRANCH)
    for file, content in REMOTE_FILES.items():
        file_path = dbt_repo_remote_path/ file
        file_path.write_text(content)
        remote.index.add(str(file_path))

    remote.index.commit("initial commit")

    _dbt_repo.create_remote("origin", remote.working_dir)
    return _dbt_repo

@pytest.fixture(scope="function")
def dbt_repo_working_dir(dbt_repo, monkeypatch):
    monkeypatch.chdir(dbt_repo.working_dir)


@pytest.fixture(scope="function")
def config_file(dbt_repo) -> Path:
    """ Path to the config.json in the dbt repo

        contains SAMPLE_CONFIG + "repo": <repo-path>
    """
    file = Path(dbt_repo.working_dir) / "config.json"
    config_with_repo = {**SAMPLE_CONFIG, **{"repo": dbt_repo.working_dir}}
    file.write_text(json.dumps(config_with_repo))
    return file


def test_remote_needs_to_be_fetched(dbt_repo: Repo):
    """Check that the local and remote repos are connected correctly"""
    assert dbt_repo.remotes.origin.exists()
    origin = dbt_repo.remotes.origin

    with pytest.raises(GitCommandError):
        for file, content in REMOTE_FILES.items():
            assert dbt_repo.git.show(f"{SAMPLE_CONFIG['branch']}:{file}") == content

    origin.fetch(REMOTE_BRANCH)
    for file, content in REMOTE_FILES.items():
        assert dbt_repo.git.show(f"{SAMPLE_CONFIG['branch']}:{file}") == content


def test_repo_content(config_file):
    """Check that the fixture is working, the repo contains the right config file"""
    assert config_file.is_file()
    config_content = json.loads(config_file.read_text())
    for k, v in SAMPLE_CONFIG.items():
        assert config_content[k] == v
    assert config_content["repo"] == str(config_file.parent)


@pytest.mark.parametrize(("argv", "dbt_args"), [
    (["dbt", "run", "--state"],
     ["dbt", "run", "--state", "OUT_DIR"]),
    (["dbt", "run", "--defer"],
     ["dbt", "run", "--state", "OUT_DIR", "--defer"]),
    (["dbt", "run", "--favor-state"],
     ["dbt", "run", "--state", "OUT_DIR", "--favor-state", "--defer"]),
    (["dbt", "run", "--favor-state", "--state"],
     ["dbt", "run", "--state", "OUT_DIR", "--favor-state", "--defer"]), # dbt args have to be in this order
    (["dbt", "run", "--favor-state"],
     ["dbt", "run", "--state", "OUT_DIR", "--favor-state", "--defer"]),
])
def test_call_dbt(runner, dbt_repo, config_file, patch_execvp, dbt_repo_working_dir, argv, dbt_args):
    """ dbt is called with the correct arguments """
    dbt_args = [str(Path(dbt_repo.working_dir, SAMPLE_CONFIG["out"])) if arg == "OUT_DIR" else arg
                for arg in dbt_args]

    _ = runner.invoke(cli, ["--config", str(config_file), *argv], obj=dict())

    patch_execvp.assert_called_once_with(
        dbt_args[0],
        dbt_args,
    )


@pytest.mark.parametrize(("argv", "should_be_available", "zero_exit"), [
    (["dbt", "run", "--state"], True, True),
    (["dbt", "--favor-state"], True, True),
    (["dbt"], False, True),
    (["fetch-files"], True, True),
    (["--no-fetch", "fetch-files"], False, False),
    (["--no-fetch", "dbt"], False, True),
])
def test_dbt_also_fetches_files(runner, dbt_repo, config_file, patch_execvp, dbt_repo_working_dir,
                                argv, should_be_available, zero_exit):
    """ 1. Checks that git objects are NOT available in the 'local' repo at first
        2. Then runs the CLI
        3. Check whether git objects are available in the 'local' repo or not
    """
    _are_files_available(dbt_repo, should_be_available=False)

    result = runner.invoke(cli, ["--config", str(config_file), *argv], obj=dict())
    assert (result.exit_code == 0) if zero_exit else (result.exit_code != 0)

    _are_files_available(dbt_repo, should_be_available=should_be_available)
