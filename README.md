# dbt-auto-defer

This tool checks your dbt cli incations and, if needed, automatically pulls the latest dbt `manifest.json`
file and inserts the correct cli arguments.

### installation

Install from git (TODO: PyPi)

~~~ bash
pip install git+https://github.com/kingalban/dbt-auto-defer

# you also need dbt installed:
# pip install dbt
~~~

and add the alias to some file you will _source_ (eg `~/.bashrc`)

~~~ bash
# ~/.bashrc
alias dbt="dbt-auto-defer --branch origin/branch-name --files path/to/manifest.json --out ./target_prod dbt"
~~~


### why
[dbt](https://www.getdbt.com/) deployment and development can be improved by taking advantage
of other current deployments of your dbt project.
To take advantage of this you need to have the current `manifest.json` file that describes the other deployment.

If you store your latest `manifest.json` file in git (eg: for dbt docs deployment),
then you can use this tool to fetch the latest manifest.

### how
Once you've aliased `dbt` to this tool, `dbt-auto-defer` will be called instead of dbt,
it will check your arguments and options and if necessary download the manifest etc.
Then it will call dbt with your original command, plus any relevant state related options.

**Note:** dbt expects the option `--state <path>` to have an argument,
`dbt-auto-defer` expects no argument because it fills the path itself.

### examples

Here are a few examples comparing the command you enter with how dbt is called:

~~~ bash
# simple things are unchanged:
dbt ls
# dbt ls
dbt run -s my_model
# dbt run -s my_model

# incorrect commands are also passed along
dbt bad_command --not-an-option
# dbt bad_command --not-an-option

# Files are only fetched when needed
dbt run -s my_model+ --state
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod

# just specifying --defer is enough
dbt run -s my_model+ --defer
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod --defer

# or even just --favor-state
dbt run -s my_model+ --favor-state
# files are fetched from git remote...
# dbt run -s my_model+ --state ./target_prod --favor-state --defer
~~~
