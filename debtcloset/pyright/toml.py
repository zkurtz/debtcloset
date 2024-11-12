"""Tools to manage pyright debt in the pyproject.toml file."""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import dummio
from listwrap import align

ERROR = "error"
FILE = "file"
EXCLUDE = "exclude"
PYRIGHT = "pyright"
SEVERITY = "severity"
TOOL = "tool"

PYPROJECT_FILE = "pyproject.toml"
HEADER = f"[{TOOL}.{PYRIGHT}]"


@dataclass
class Pyproject:
    """Parsing a pyproject.toml to access the [tool.pyright] section."""

    content: str

    def __post_init__(self) -> None:
        """Add the [tool.pyright] section if it's not already there."""
        if HEADER not in self.content:
            # Add such a section at the end of the file separated [above] by an empty line:
            self.content += f"\n{HEADER}\n"

    @classmethod
    def from_file(cls, filepath: Path) -> "Pyproject":
        """Create a Pyproject instance from a file path."""
        return cls(content=dummio.text.load(filepath))

    def save(self, filepath: Path) -> None:
        """Save the Pyproject instance to a file path."""
        dummio.text.save(self.content, filepath=filepath)

    @property
    def where_start_pyright_section(self) -> int:
        """Find the location of the first character of the HEADER section."""
        return self.content.index(HEADER)

    @property
    def where_end_pyright_section(self) -> int:
        """Find the location of the first character after the HEADER section."""
        start = self.where_start_pyright_section
        n_header = len(HEADER)
        remainder = self.content[(start + n_header) :]
        next_section_pattern = "\n["
        if next_section_pattern not in remainder:
            return len(self.content)
        return start + n_header + remainder.index(next_section_pattern)

    def __call__(self) -> str:
        """Extract the [tool.pyright] section from the content."""
        start = self.where_start_pyright_section
        end = self.where_end_pyright_section
        return self.content[start:end]

    def replace(self, new_content: str) -> "Pyproject":
        """Replace the [tool.pyright] section with new content."""
        start = self.where_start_pyright_section
        end = self.where_end_pyright_section
        return Pyproject(content=self.content[:start] + new_content + self.content[end:])


@dataclass
class Pyright:
    """Manage manipulations of the [tool.pyright] section."""

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


def remove_exclusions(repo_root: str = os.getcwd()) -> None:
    """Remove any pyright exclusions file from the pyproject.toml file."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    pyproject = Pyproject.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.remove_exclusions()
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def set_exclusions(repo_root: str = os.getcwd(), *, files: list[str]) -> None:
    """Add exclusions to the pyproject.toml file."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    pyproject = Pyproject.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.add_exclusions(files)
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def run_pyright(repo_root: str, required_exclusions: list[str]) -> list[str]:
    """Runs pyright and returns a list of file paths with errors."""
    set_exclusions(repo_root, files=required_exclusions)
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        cmd = [PYRIGHT, "--outputjson"]
        with open(tmpfile.name, "w") as file:
            subprocess.run(cmd, stdout=file, cwd=repo_root)
        output = dummio.json.load(tmpfile.name)
    remove_exclusions(repo_root)
    diagnostics = output["generalDiagnostics"]
    fullpaths = set([item[FILE] for item in diagnostics if item[SEVERITY] == ERROR])
    len_prefix = len(repo_root) + 1
    return sorted([path[len_prefix:] for path in fullpaths])


def exclude(repo_root: str = os.getcwd(), required_exclusions: list[str] | None = None) -> None:
    """Reconfigure pyproject.toml to exclude all files where pyright throws any errors."""
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    if not pyproject_toml_path.exists():
        raise FileNotFoundError(f"Could not find {pyproject_toml_path}")
    remove_exclusions(repo_root)
    required_exclusions = required_exclusions or []
    exclude_files = run_pyright(repo_root, required_exclusions=required_exclusions)
    set_exclusions(repo_root, files=required_exclusions + exclude_files)
