"""Loads configuration for Cocoa from pyproject.toml."""

import sys
from pathlib import Path

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

# Config names mapped to argparse.ConfigParser.add_argument()
# keyword arguments dictionaries
DEFAULT_CONFIG = {
    "max_cells_per_notebook": {
        "help": "Maximum number of cells allowed in a Jupyter Notebook",
        "type": int,
        "default": 10,
    },
    "max_lines_per_cell": {
        "help": "Maximum number of lines allowed in a Jupyter Notebook Cell",
        "type": int,
        "default": 15,
    },
    "max_functions_per_notebook": {
        "help": "Maximum number of function definitions per notebook",
        "type": int,
        "default": 0,
    },
    "ruff_select": {
        "help": "Ruff linter select options",
        "type": str,
        "default": "ANN,B,C4,D,I,N801,N804,N805,PD,PLR2004,PTH,W,S,UP,YTT",
    },
    "ruff_ignore": {
        "help": "Ruff linter ignore options",
        "type": str,
        "default": "D415,ANN002,ANN003,ANN101,ANN102,B905",
    },
    "verbose": {
        "help": "Print all results",
        "default": False,
        "action": "store_true",
    },
    "start_date": {
        "help": "Start date in YYYY-MM-DD format to filter files by commit date",
        "type": str,
        "default": None,
    },
    "branchinfo": {
        "help": "Report branch information",
        "default": False,
        "action": "store_true",
    },
    "branch_name": {
        "help": "Branch name to evaluate",
        "type": str,
        "default": "main",
    },
}


def load_config(repo_path: Path | str) -> dict:
    """Loads configuration from pyproject.toml, using defaults if necessary.

    Args:
        repo_path: The path to the repository to load configuration from.

    Returns:
        A dictionary containing the configuration settings.
    """
    repo_path = Path(repo_path)
    pyproject_path = repo_path / "pyproject.toml"
    config = {key: value["default"] for key, value in DEFAULT_CONFIG.items()}

    if pyproject_path.exists():
        try:
            with pyproject_path.open("rb") as f:
                pyproject_data = tomllib.load(f)
            cocoa_config = pyproject_data.get("tool", {}).get("cocoa", {})

            # Merge user config with defaults, converting keys
            for key, value in cocoa_config.items():
                # Convert kebab-case keys from pyproject.toml to snake_case
                snake_case_key = key.replace("-", "_")
                if snake_case_key in config:
                    config[snake_case_key] = value
                else:
                    print(f"Warning: Unknown configuration key '{key}' in [tool.cocoa]")
        except tomllib.TOMLDecodeError as e:
            print(f"Error parsing {pyproject_path}: {e}")
        except Exception as e:
            print(f"Error loading configuration from {pyproject_path}: {e}")

    return config
