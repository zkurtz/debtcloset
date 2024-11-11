"""Main tests of dummio."""

import textwrap
from pathlib import Path

from debtcloset.ruff import toml

INPUT_STR = """
    [build-system]
    requires = [ "poetry-core>=1.0.0",]
    build-backend = "poetry.core.masonry.api"

    [tool.ruff]
    line-length = 120

    [tool.faketool]
    blah = "blah"
    """

EXPECTED_STR = """
    [build-system]
    requires = [ "poetry-core>=1.0.0",]
    build-backend = "poetry.core.masonry.api"

    [tool.ruff]
    line-length = 120
    extend-exclude = [
        "src/module1.py",
        "src/module2.py",
    ]

    [tool.faketool]
    blah = "blah"
    """


def test_exclude(tmp_path: Path) -> None:
    """Verify expected behaviour."""

    # Create a dummy python repo including multiple files with unused package imports:
    pyproject_file = tmp_path / "pyproject.toml"
    pyproj_str = textwrap.dedent(INPUT_STR)
    pyproject_file.write_text(pyproj_str)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    module1 = src_dir / "module1.py"
    module2 = src_dir / "module2.py"
    module3 = src_dir / "module3.py"
    module1.write_text("import os")
    module2.write_text("import os")
    module3.write_text("print('hello')")

    toml.exclude(repo_root=str(tmp_path))
    result_str = pyproject_file.read_text()
    assert result_str == textwrap.dedent(EXPECTED_STR)
