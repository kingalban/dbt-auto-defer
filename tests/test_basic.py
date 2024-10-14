
from dbt_auto_defer import cli

def test_version(runner):
    """ Does the CLI show the right version? """
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == 'dbt-auto-defer, version 0.1.0\n'


def test_help(runner):
    """ Does the CLI show some help successfully? """
    explicit_result = runner.invoke(cli, ["--help"])
    implicit_result = runner.invoke(cli, ["--help"])
    assert explicit_result.exit_code == 0
    assert implicit_result.exit_code == 0
    assert len(explicit_result.output) > 10
    assert implicit_result.output == explicit_result.output
