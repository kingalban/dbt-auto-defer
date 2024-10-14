
import pytest
from click.testing import CliRunner

@pytest.fixture(scope="session")
def runner():
    return CliRunner()

@pytest.fixture(scope="function")
def patch_execvp(mocker):
    return mocker.patch('dbt_auto_defer.execvp')
