from __future__ import annotations

from pathlib import Path
from typing import Any
from git import Repo
import click
from click.core import ParameterSource
import json
import sys

CONFIG_MARKER = ".config_from_file"
CONFIG_OPTION = "config"

# borrowed from https://github.com/asottile/awshelp
if sys.platform == "win32":
    import subprocess

    def execvp(cmd: str, args: list[str]) -> int:
        return subprocess.call(args)
else:
    from os import execvp


class OptionDefaultFromConfig(click.Option):
    def get_default(self, ctx: click.Context, call: bool = True) -> str:
        if CONFIG_OPTION in ctx.params and ctx.params[CONFIG_OPTION].exists():
            if CONFIG_MARKER not in ctx.obj:
                ctx.obj[CONFIG_MARKER] = json.loads(ctx.params[CONFIG_OPTION].read_text())
            if self.name in ctx.obj[CONFIG_MARKER]:
                return ctx.obj[CONFIG_MARKER][self.name]
        return super().get_default(ctx, call)


@click.group(context_settings={'show_default': True})
@click.pass_context
@click.version_option(prog_name="dbt-auto-defer")
@click.option(f"-{CONFIG_OPTION[0]}", f"--{CONFIG_OPTION}", required=False, default=".dbt-auto-defer.json",
              type=click.Path(dir_okay=False, path_type=Path),
              help="json file containing configurations, overwritten by the other options")
@click.option("-b", "--branch", default="origin/gh-pages", help="branch to get files from", cls=OptionDefaultFromConfig)
@click.option("-f", "--files", multiple=True, default=["docs/manifest.json"], help="files to output", cls=OptionDefaultFromConfig)
@click.option("-o", "--out", default="target_prod", type=click.Path(exists=False), help="path to save file in", cls=OptionDefaultFromConfig)
@click.option("-r", "--repo", default=".", type=click.Path(exists=True), help="path to repo root", cls=OptionDefaultFromConfig)
@click.option("--fetch/--no-fetch", default=True, help="whether to first fetch the remote")
@click.option("--debug/--no-debug", default=False, help="print all actions taken")
def cli(ctx, debug: bool, config: Path, **kwargs: Any) -> None:
    def log(*a, **k):
        if debug:
            click.echo(*a, **k, err=True)

    if ctx.get_parameter_source(CONFIG_OPTION) is not ParameterSource.DEFAULT \
        and not config.exists():
        click.echo(f"Specified config file '{config!s}' was not found!", err=True)

    ctx.obj["log"] = log
    ctx.obj.update(kwargs)


@cli.command()
@click.pass_context
def fetch_files(ctx):
    """Fetch the files from git and print the dir containing them"""
    log = ctx.obj["log"]
    repo = Repo(ctx.obj["repo"], search_parent_directories=True)

    if ctx.obj["fetch"]:
        if "/" not in ctx.obj["branch"]:
            raise click.exceptions.BadOptionUsage(option_name="--branch",
                                                  message="branch should specify a remote branch like "
                                                          f"'<remote-name>/<branch-name>', not {ctx.obj['branch']!r}.\n"
                                                          f"If you're not fetching from a remote, specify '--no-fetch'")
        remote_name, _, branch_name = ctx.obj["branch"].partition("/")

        try:
            remote = repo.remote(remote_name)
        except ValueError:
            raise click.exceptions.BadOptionUsage(option_name="--branch",
                                                  message=f"Could not find remote {remote_name!r}")

        log(f"{remote=!r}, {branch_name=!r}")
        remote.fetch(branch_name)

    out_path = Path(ctx.obj["out"])
    out_path.mkdir(parents=True, exist_ok=True)

    for file in ctx.obj["files"]:
        log(f"outputting: {ctx.obj['branch']}:{file}")
        Path(out_path, Path(file).name).write_text(repo.git.show(f"{ctx.obj['branch']}:{file}"))
    dir_name = click.format_filename(out_path.absolute())
    return dir_name


@cli.command(context_settings={"ignore_unknown_options": True})
@click.pass_context
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--state", default=False, is_flag=True, help="automatically fetch and use prod state")
@click.option("--favor-state", default=False, is_flag=True)
@click.option("--defer", default=False, is_flag=True)
def dbt(ctx, args, state, favor_state, defer):
    """Runs dbt, automatically inserting the current --state

    dbt is run (by name), if a --state related option is supplied
    then the latest state is pulled and the path inserted into
    dbt's argv.

    eg:
        `dbt-auto-defer dbt run -s my_model --favor-state`
     => `dbt run -s my_model --state ./target_prod --favor-state --defer`
    """
    log = ctx.obj["log"]
    cmd = ["dbt"] + list(args)

    if state or favor_state or defer:
        state_dir = ctx.invoke(fetch_files)
        cmd += ["--state", state_dir]
        if favor_state:
            cmd += ["--favor-state", "--defer"]
        elif defer:
            cmd += ["--defer"]

    log(f"executing: {' '.join(cmd)!r}")

    return execvp(cmd[0], cmd)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
