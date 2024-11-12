# dbt-auto-defer

Save time without compromise when developing dbt projects!

This tool checks your dbt cli invocations and, _if needed_,
automatically pulls the latest dbt `manifest.json` file and inserts
the correct cli arguments to defer to another deployment.

Your `dbt build` finishes faster, and you didn't have to work for it.

## installation

This tool can be installed in the virtual environment of your project,
or globally on your system.
Because `dbt` is called by name,
you don't need to install both tools in the same place,
but it has to be available.

Install from git:

~~~ bash
pip install git+https://github.com/kingalban/dbt-auto-defer

# you also need dbt installed:
# pip install dbt
~~~

### settings

The specifics of the git remote, etc. can be set either in a JSON file
(default `./.dbt-auto-defer.json`) or, with precedent, by CLI arguments.

Some of these have default values. As always,
you can learn more from `dbt-auto-defer --help`.

~~~ json
{
    "branch": "origin/<branch name>",
    "repo": "<local path>",
    "out": "<out path>",
    "files": ["<path to manifest.json>", "<another path>"]
}
~~~

To fully integrate this into your workflow, you can alias `dbt` to this tool.
Just add the alias to some file you will _source_ (eg `~/.bashrc`).
Once you've set the alias, you don't need to do anything more to call this tool,
it will just help you when you need it, and stay out of your way when you don't.

~~~ bash
# ~/.bashrc
alias dbt="dbt-auto-defer dbt"
~~~

__Tip__: if you're working with one dbt project you
can provide the settings _in_ the alias.
If you're using multiple dbt project,
you can store the configuration for each one in their project files.
Or even mix the two, if it suits you!

### why

[dbt](https://www.getdbt.com/) deployment and development can be improved by
taking advantage of _other_ deployments of your dbt project.
To take advantage of this you need to have the current `manifest.json`
file that describes the other deployment.

You can find dbt's own defer docs [here](https://docs.getdbt.com/reference/node-selection/defer).

To take advantage of this you need to have the current `manifest.json`
file that describes the other deployment.
If you store your latest `manifest.json` file in git (eg: for dbt docs deployment),
then you can use this tool to fetch the latest manifest.

Here's an example of how using dbt's defer feature can shrink a deployment.
If the developer wants to try a new version of the model `C`,
normally they would have to build at least `a` and `b`.
When defering to the production deployment,
the `dev` version of `C` will actually be build
using the `prod` instances of `a`, and `b`.

To be explicit, assuming your default profile is `dev`,
this is achieved with just the command: `dbt-auto-defer dbt run -m C`

<img src="./diagrams/dbt-defer.svg">

## how

When you call `dbt` with this tool,
`dbt-auto-defer` will check your arguments and
options, and if necessary download the manifest.
Then it will call dbt with your original command,
plus any relevant state related options.

_Note:_ dbt expects the option `--state <path>` to have an argument,
`dbt-auto-defer` expects no argument because it fills the path itself.

## examples

Here are a few examples comparing the command you enter with how dbt is called
(here, the alias `dbt="dbt-auto-defer dbt` is in effect):

~~~ bash
# simple things are unchanged:
dbt ls
# dbt ls
dbt run -s my_model
# dbt run -s my_model

# incorrect commands are also passed along
dbt bad_command --not-an-option
# dbt bad_command --not-an-option

# files are only fetched when needed
dbt run -s my_model+ --state
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod

# just specifying --defer is enough
dbt run -s my_model+ --defer
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod --defer

# or even just --favor-state!
dbt run -s my_model+ --favor-state
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod --favor-state --defer
~~~
