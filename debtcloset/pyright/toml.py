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


def remove_exclusions(pyproject_toml_path: Path) -> None:
    """Remove any pyright exclusions file from the pyproject.toml file."""
    pyproject = Pyproject.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.remove_exclusions()
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def set_exclusions(pyproject_toml_path: Path, *, files: list[str]) -> None:
    """Add exclusions to the pyproject.toml file."""
    pyproject = Pyproject.from_file(pyproject_toml_path)
    config = Pyright(pyproject())
    new_config = config.add_exclusions(files)
    new_pyproject = pyproject.replace(new_config)
    new_pyproject.save(filepath=pyproject_toml_path)


def identify_failing_modules(repo_root: Path, required_exclusions: list[str]) -> list[str]:
    """Runs pyright and returns a list of file paths with errors.

    Overall approach:
    1. Update pyproject.toml to exclude the `required_exclusions` paths for pyright.
    2. Run pyright and compile the list of files with errors.
    3. Reset pyproject.toml to its original state (without exclusions).
    4. Return the list of files with errors.

    Args:
        repo_root: The path to the repository root.
        required_exclusions: A list of file paths to exclude from the analysis.
    """
    pyproject_toml_path = Path(repo_root) / PYPROJECT_FILE
    set_exclusions(pyproject_toml_path, files=required_exclusions)
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        cmd = [PYRIGHT, "--outputjson"]
        with open(tmpfile.name, "w") as file:
            subprocess.run(cmd, stdout=file, cwd=repo_root)
        output = dummio.json.load(tmpfile.name)
    remove_exclusions(pyproject_toml_path)
    diagnostics = output["generalDiagnostics"]
    fullpaths = set([item[FILE] for item in diagnostics if item[SEVERITY] == ERROR])
    len_prefix = len(str(repo_root)) + 1
    relpaths = sorted([path[len_prefix:] for path in fullpaths])
    # If the paths were generated on windows, we need to convert them to unix-style paths:
    return [path.replace(os.sep, "/") for path in relpaths]


def compile_ignores(repo_root: Path, required_exclusions: list[str] | None = None) -> list[str]:
    """Compile a list of files/directories that we want pyright to ignore."""
    default_ignored_directories = [
        ".venv",
        ".tox",
        "docs",
    ]
    ignores = []
    for item in default_ignored_directories:
        path = repo_root / item
        if path.is_dir():
            ignores.append(f"{item}/*")
    additional_required_ignores = set(required_exclusions or []) - set(ignores)
    return sorted(ignores + list(additional_required_ignores))


def exclude(repo_root: str = os.getcwd(), required_exclusions: list[str] | None = None) -> None:
    """Reconfigure pyproject.toml to exclude all files where pyright throws any errors."""
    repo_root_path = Path(repo_root)
    pyproject_toml_path = repo_root_path / PYPROJECT_FILE
    if not pyproject_toml_path.exists():
        raise FileNotFoundError(f"Could not find {pyproject_toml_path}")
    remove_exclusions(pyproject_toml_path)
    ignores = compile_ignores(repo_root_path, required_exclusions=required_exclusions)
    failures = identify_failing_modules(repo_root_path, required_exclusions=ignores)
    set_exclusions(pyproject_toml_path, files=ignores + failures)
