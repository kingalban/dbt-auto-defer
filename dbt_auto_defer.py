from __future__ import annotations

from pathlib import Path

from git import Repo
import click
import sys

# borrowed from https://github.com/asottile/awshelp
if sys.platform == "win32":
    import subprocess

    def execvp(cmd: str, args: list[str]) -> int:
        return subprocess.call(args)
else:
    from os import execvp


@click.group
@click.pass_context
@click.option("-b", "--branch", type=str, help="branch to get files from")
@click.option("-f", "--files", multiple=True, default=["docs/manifest.json"], help="files to output")
@click.option("-o", "--out", default="target_prod", type=click.Path(exists=False), help="path to save file in")
@click.option("-r", "--repo", default=".", type=click.Path(exists=True), help="path to repo root")
@click.option("--fetch/--no-fetch", default=True, help="whether to first fetch the remote")
@click.option("--debug/--no-debug", default=False, help="print all actions taken")
def cli(ctx, debug, **kwargs):
    def log(*a, **k):
        if debug:
            click.echo(*a, **k, err=True)

    ctx.obj.update(kwargs)
    ctx.obj["log"] = log


@cli.command()
@click.pass_context
def fetch_files(ctx):
    """Fetch the files from git and print the dir containing them"""
    log = ctx.obj["log"]
    repo = Repo(ctx.obj["repo"])

    if ctx.obj["fetch"]:
        for remote in repo.remotes:
            log(f"remote is: {remote!r}")
            remote.fetch(ctx.obj["branch"].split("/")[-1])

    out_path = Path(ctx.obj["out"])
    out_path.mkdir(parents=True, exist_ok=True)

    for file in ctx.obj["files"]:
        log(f"outputting: {ctx.obj['branch']}:{file}")
        Path(out_path, Path(file).name).write_text(
            repo.git.show(f"{ctx.obj['branch']}:{file}")
        )
    dir_name = click.format_filename(out_path.absolute())
    return dir_name


@click.pass_context
@cli.command(context_settings={"ignore_unknown_options": True})
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
