"""Main tests of dummio."""

import shutil
import textwrap
from pathlib import Path

from debtcloset import REPO_DIR
from debtcloset.pyright import toml

INPUT_STR = """
    [build-system]
    requires = [ "poetry-core>=1.0.0",]
    build-backend = "poetry.core.masonry.api"

    [tool.pyright]

    [tool.faketool]
    blah = "blah"
    """

EXPECTED_STR = """
    [build-system]
    requires = [ "poetry-core>=1.0.0",]
    build-backend = "poetry.core.masonry.api"

    [tool.pyright]
    exclude = [
        "src/module1.py",
        "src/module2.py",
    ]

    [tool.faketool]
    blah = "blah"
    """

EXPECTED_STR_REQ = """
    [build-system]
    requires = [ "poetry-core>=1.0.0",]
    build-backend = "poetry.core.masonry.api"

    [tool.pyright]
    exclude = [
        "subdir/*",
        "src/module2.py",
    ]

    [tool.faketool]
    blah = "blah"
    """


def _build_dummy_repo(pyproject_file: Path, use_subdir: bool = False) -> None:
    """Build a dummy python repo including multiple files including some type errors."""
    directory = pyproject_file.parent
    # Empty directory of all contents (but keeping the directory), using shutil:
    shutil.rmtree(directory)
    directory.mkdir()
    pyproject_file.write_text(textwrap.dedent(INPUT_STR))
    src_dir = directory / "src"
    src_dir.mkdir()
    module1 = src_dir / "module1.py"
    module2 = src_dir / "module2.py"
    module3 = src_dir / "module3.py"
    module1.write_text("num: str = 2")
    module2.write_text("num: float = str(2)")
    module3.write_text("print('hello')")
    if use_subdir:
        sub_dir = directory / "subdir"
        sub_dir.mkdir()
        shutil.move(directory / "src" / "module1.py", sub_dir)


def test_exclude(tmp_path: Path) -> None:
    """Verify expected behaviour."""
    pyproject_file = tmp_path / "pyproject.toml"
    _build_dummy_repo(pyproject_file)
    toml.exclude(repo_root=str(tmp_path))
    result_str = pyproject_file.read_text()
    assert result_str == textwrap.dedent(EXPECTED_STR)

    # Verify that we can apply a "required exclusion", superseding the "found" exclusions:
    _build_dummy_repo(pyproject_file, use_subdir=True)
    toml.exclude(repo_root=str(tmp_path), required_exclusions=["subdir/*"])
    result_str = pyproject_file.read_text()
    assert result_str == textwrap.dedent(EXPECTED_STR_REQ)

    # But `subdir/module1.py` still needs to be explicitly excluded if we skip the `subdir/*` exclusion:
    _build_dummy_repo(pyproject_file, use_subdir=True)
    toml.exclude(repo_root=str(tmp_path))
    result_str = pyproject_file.read_text()
    assert "module1.py" in result_str

    # This repo runs pyright as part of CI, so the pyproject.toml should not have a pyright exclude list, and running
    # exclude should have no effect:
    pyproject_file = REPO_DIR / "pyproject.toml"
    original_pyproject = pyproject_file.read_text()
    toml.exclude(repo_root=str(REPO_DIR))
    final_pyproject = pyproject_file.read_text()
    assert original_pyproject == final_pyproject
