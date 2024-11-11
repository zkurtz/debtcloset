"""Main tests of dummio."""

from debtcloset import REPO_DIR
from debtcloset.pyright import toml


def test_exclude() -> None:
    """Verify expected behaviour."""

    # This repo runs pyright as part of CI, so the pyproject.toml should not have a pyright exclude list, and running
    # exclude should have no effect:
    pyproject_file = REPO_DIR / "pyproject.toml"
    original_pyproject = pyproject_file.read_text()
    toml.exclude(repo_root=str(REPO_DIR))
    final_pyproject = pyproject_file.read_text()
    assert original_pyproject == final_pyproject
