"""Tools to manage ruff debt in the pyproject.toml file."""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import dummio
from listwrap import align

ERROR = "error"
FILENAME = "filename"
EXCLUDE = "extend-exclude"
RUFF = "ruff"
SEVERITY = "severity"
TOOL = "tool"

PYPROJECT_FILE = "pyproject.toml"
HEADER = f"[{TOOL}.{RUFF}]"


@dataclass
class Ruff:
    """Parsing a pyproject.toml to access the [tool.ruff] section."""

    content: str

    def __post_init__(self) -> None:
        """Add the [tool.ruff] section if it's not already there."""
        if HEADER not in self.content:
            # Add such a section at the end of the file separated [above] by an empty line:
            self.content += f"\n{HEADER}\n"

    @classmethod
    def from_file(cls, filepath: Path) -> "Ruff":
        """Create a Ruff instance from a file path."""
        return cls(content=dummio.text.load(filepath))

    def save(self, filepath: Path) -> None:
        """Save the Ruff instance to a file path."""
        dummio.text.save(self.content, filepath=filepath)

    @property
    def where_start_ruff_section(self) -> int:
        """Find the location of the first character of the HEADER section."""
        return self.content.index(HEADER)

    @property
    def where_end_ruff_section(self) -> int:
        """Find the location of the first character after the HEADER section."""
        start = self.where_start_ruff_section
        n_header = len(HEADER)
        remainder = self.content[(start + n_header) :]
        next_section_pattern = "\n["
        if next_section_pattern not in remainder:
            return len(self.content)
        return start + n_header + remainder.index(next_section_pattern)

    def __call__(self) -> str:
        """Extract the [tool.ruff] section from the content."""
        start = self.where_start_ruff_section
        end = self.where_end_ruff_section
        return self.content[start:end]

    def replace(self, new_content: str) -> "Ruff":
        """Replace the [tool.ruff] section with new content."""
        start = self.where_start_ruff_section
        end = self.where_end_ruff_section
        return Ruff(content=self.content[:start] + new_content + self.content[end:])


@dataclass
class Pyright:
    """Manage manipulations of the [tool.ruff] section."""

    content: str

    def __post_init__(self) -> None:
        """Add the `exclude` line if it's not already there."""
        if EXCLUDE not in self.content:
            self.content += f"\n{EXCLUDE} = []"

    @property
    def start_exclude(self) -> int:
        """Find the location of the first character of the `exclude` line."""
        return self.content.index(f"\n{EXCLUDE}")

    @property
    def end_exclude(self) -> int:
        """Find the location of the first character after the `exclude` section."""
        start = self.start_exclude
        remainder = self.content[start:]
        next_section_pattern = "]"
        return start + remainder.index(next_section_pattern) + 1

    def remove_exclusions(self) -> str:
        """Remove the `exclude` line(s) from the content."""
        start = self.start_exclude
        end = self.end_exclude
        return self.content[:start] + self.content[end:]

    def add_exclusions(self, files: list[str]) -> str:
        """Remove any pre-existing exclusions and append new ones."""
        content = self.remove_exclusions()
        if not files:
            return content
        excl_str = f"{EXCLUDE} = [\n{align(files)}\n]\n"
        if not content.endswith("\n"):
            excl_str = "\n" + excl_str
        return content + excl_str


def run_ruff(repo_root: str) -> list[str]:
    """Runs ruff and returns a list of file paths with errors."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        cmd = [RUFF, "check", repo_root, "--output-format=json"]
        with open(tmpfile.name, "w") as file:
            subprocess.run(cmd, stdout=file, cwd=repo_root)
        output = dummio.json.load(tmpfile.name)
    if not output:
        return []
    fullpaths = set([item[FILENAME] for item in output])
    len_prefix = len(repo_root) + 1
    return sorted([path[len_prefix:] for path in fullpaths])


def remove_exclusions(repo_root: str = os.getcwd()) -> None:
    """Remove any ruff exclusions file from the pyproject.toml file."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    pyproject = Ruff.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.remove_exclusions()
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def add_exclusions(repo_root: str = os.getcwd(), *, files: list[str]) -> None:
    """Add exclusions to the pyproject.toml file."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    pyproject = Ruff.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.add_exclusions(files)
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def exclude(repo_root: str = os.getcwd()) -> None:
    """Reconfigure pyproject.toml to exclude all files where ruff throws any errors."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    if not pyproject_toml_path.exists():
        raise FileNotFoundError(f"Could not find {pyproject_toml_path}")
    remove_exclusions(repo_root)
    exclude_files = run_ruff(repo_root)
    if exclude_files:
        add_exclusions(repo_root, files=exclude_files)
