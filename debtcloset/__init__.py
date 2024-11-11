"""Initialize debtcloset package."""

from importlib.metadata import version
from pathlib import Path

__version__ = version("debtcloset")
SRC_DIR = Path(__file__).parent
REPO_DIR = SRC_DIR.parent
