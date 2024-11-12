# debtcloset

Creation and maintenance of "exclude" file lists for common code quality tools.

Integrating a new code quality tool in an established repo typically requires a transitional period of ignoring/excluding a significant fraction of files for pre-commit checks or continuous integration testing. During such a transition, your technical "debt closet" is the collection of excluded files. `debtcloset` streamlines the creating and maintenance of your debt closet and includes tools to keep it up-to-date to reflect code changes.

## Quick start

We're [on pypi](https://pypi.org/project/debtcloset/) so you can just `pip install debtcloset` or `poetry add debtcloset` etc.

### pyright with pyproject.toml

To update your pyproject.toml's pyright configuration to exclude all files that currently fail pyright checks, simply do

```
from debtcloset.pyright.toml import exclude
exclude()
```

### ruff with pyproject.toml

To update your pyproject.toml's pyright configuration to exclude all files that currently fail ruff checks, simply do

```
from debtcloset.ruff.toml import exclude
exclude()
```

## Development

Install poetry:
```
curl -sSL https://install.python-poetry.org | python3 -
```

Install [pyenv and its virtualenv plugin](https://github.com/pyenv/pyenv-virtualenv). Then:
```
pyenv install 3.12.2
pyenv global 3.12.2
pyenv virtualenv 3.12.2 debtcloset
pyenv activate debtcloset
```

Install this package and its dependencies in your virtual env:
```
poetry install --with extras --with dev
```

Set up git hooks:
```
pre-commit install
```
