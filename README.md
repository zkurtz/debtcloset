# debtcloset

Gradually roll out ruff and/or pyright to your Python codebase with minimal disruption. `debtcloset` helps you adopt code quality tooling without overwhelming your team or missing deadlines.

Here's how you can up-level your repo's code quality using `debtcloset`:
1. Start using a `pyproject.toml` file for your project if you don't already.
1. `pip install` (or `uv add` etc) debtcloset plus ruff and/or pyright.
1. Configure ruff and/or pyright in your `pyproject.toml`. If you have no idea where to start, consider just copy-pasting these configs:
    1. [ruff](https://github.com/zkurtz/honor-code/blob/e9c1ba2bc98369f98f293771248feb86bc901c6f/software/python/pyproject.toml#L59-L84)
    1. [pyright](https://github.com/zkurtz/honor-code/blob/e9c1ba2bc98369f98f293771248feb86bc901c6f/software/python/pyproject.toml#L53-L55)
1. Use `debtcloset` to update your configs to ignore errors for all files that currently fail any ruff and pyright checks:
    ```
    from debtcloset.ruff.toml import exclude as ruff_exclude
    from debtcloset.pyright.toml import exclude as pyright_exclude

    ruff_exclude()
    pyright_exclude()
    ```
1. Add ruff/pyright to your pre-commit hooks and/or CI workflows.

You can land all these changes with zero disruption to your team, since any pre-existing errors remain ignored until you choose to address them. The `exclude` lists of files that debtcloset added to your pyproject.toml show you what needs to be fixed, and you can address them at your own pace. Meanwhile, any new modules will by default be checked by ruff and pyright, preventing the introduction of new issues.

Q&A:
- **Why not just fix all the errors?** If you're capable of that, then just do it, don't use debtcloset!
- **Should I include calls to debtcloset in my pre-commit hooks?** Absolutely not. debtcloset is a one-time tool to help you get started with ruff and pyright. Once you've run it, you should remove the calls to debtcloset from your codebase. (However, it can be useful to occasionally re-run debtcloset to identify any files that have been removed or fixed but failed to get removed from the exclude lists.)
- **What's the point of using ruff/pyright if you're just going to ignore all the errors?** Although it's true that debcloset ignores pre-existing errors, your ruff/pyright checks will still catch new errors in any new or already error-free as they're introduced. The point is to minimize future damage. It's still on you to prioritize and burn down your exclude lists over time.

We're [on pypi](https://pypi.org/project/debtcloset/). Consider using the [simplest-possible virtual environment](https://gist.github.com/zkurtz/4c61572b03e667a7596a607706463543) if working directly on this repo.
