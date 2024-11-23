# debtcloset

Creation and maintenance of "exclude" file lists for common code quality tools.

Integrating a new code quality tool in an established repo typically requires a transitional period of ignoring/excluding a significant fraction of files for pre-commit checks or continuous integration testing. During such a transition, your technical "debt closet" is the collection of excluded files. `debtcloset` streamlines the creating and maintenance of your debt closet and includes tools to keep it up-to-date to reflect code changes.

## Quick start

We're [on pypi](https://pypi.org/project/debtcloset/) so you can just `pip install debtcloset` or `poetry add debtcloset` etc.

### pyright with pyproject.toml

Update your pyproject.toml's pyright configuration to exclude all files that currently fail pyright checks:

```
from debtcloset.pyright.toml import exclude
exclude()
```

### ruff with pyproject.toml

Update your pyproject.toml's pyright configuration to exclude all files that currently fail ruff checks:

```
from debtcloset.ruff.toml import exclude
exclude()
```

## Development

```
git clone git@github.com:zkurtz/debtcloset.git
cd debtcloset
pip install uv
uv sync
source .venv/bin/activate
pre-commit install
```
