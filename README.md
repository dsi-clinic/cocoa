# Clinic Opinionated Codebase Oversight and Analysis

[![Cocoa Error Analysis](https://github.com/dsi-clinic/cocoa/actions/workflows/error.badges.yml/badge.svg)](https://github.com/dsi-clinic/cocoa/actions/workflows/error.badges.yml)

[![Pre-commit](https://github.com/dsi-clinic/cocoa/actions/workflows/main.workflow.yml/badge.svg)](https://github.com/dsi-clinic/cocoa/actions/workflows/main.workflow.yml)

This repository was developed in order to generate automated reports on how well codebases adhere to the [coding standards](https://github.com/dsi-clinic/coding-standards) of the University of Chicago's DSI [Clinic course](https://datascience.uchicago.edu/education/data-science-clinic/).

The goal of this codebase is to provide a quick and easy way to review code and to alert contributors where their code may be failing.

## Installation
This package depends on `ruff` being available in your environment.

```bash
python3 -m pip install dsi-cocoa ruff==0.4.10
```

## cocoa

This package contains a module `evaluate_repo` which runs code testing libraries against a repository. There are multiple ways that we want to be able to run this repo:

1. We want to be able to clone `cocoa` and then use it as part of their process.
2. We want administrators to be able to give it a list of repos to generate reports on all repos.
3. (Eventually) We want it to be able to run as a github action _on the repo itself_.
4. (Eventually) We want to be able to have adminstrative repo that can run it on other repos.

### How to run

Via command line:

```bash
cocoa /path/to/repo
```

#### Configuration

Cocoa can be configured via command-line arguments or through a `pyproject.toml` file in the root of the repository being analyzed. Command-line arguments always override settings in `pyproject.toml`.

**Command-Line Options:**

- `repo`: (Required) Path to the repository directory or a Git URL.
- `--verbose`: Print all linting results instead of truncating (default: `False`).
- `--branch <branch-name>`: Specify the branch to evaluate (default: `main`).
- `--branchinfo`: Report detailed information about remote branches (default: `False`).
- `--date <YYYY-MM-DD>`: Only analyze files committed on or after this date (defualt: `None`).
- `--max-cells-per-notebook`: Maximum number of cells allowed in a Jupyter Notebook (default: `10`).
- `--max-lines-per-cell`: Maximum number of lines allowed in a Jupyter Notebook Cell (default: `15`).
- `--max-functions-per-notebook`: Maximum number of function definitions per notebook (default: `0`).

**`pyproject.toml` Options:**

Create a `[tool.cocoa]` section in your `pyproject.toml` file. Each option for the command line is an option in the pyproject.toml. Example file:

```toml
[tool.cocoa]
# General settings
verbose = false
date = "YYYY-MM-DD"  # Optional: same as --date
branchinfo = false
branch = "main"

# Notebook specific limits
max-cells-per-notebook = 10
max-lines-per-cell = 15
max-functions-per-notebook = 0
```

**Example Usage:**

Results are truncated by default. To print all results, use the verbose option:

```bash
cocoa /path/to/repo --verbose
```

Cocoa evaluates the main branch by default. To evaluate a different branch, use the branch argument:

```bash
cocoa /path/to/repo --branch branch-name
```


To evaluate files created or modified after a certain date, use the date option:

```bash
cocoa /path/to/repo --date YYYY-MM-DD
```

All options can be combined like so:

```bash
cocoa /path/to/repo --verbose --branch <branch-name> --date YYYY-MM-DD
```


### Checks

The code run multiple checks on each repo. For each check run there are three possibilities:

1. WARNING: Most likely this needs to be fixed.
1. INFO: Log information for additional context.
1. ERROR: A critical issue that needs to be addressed.

For each of the checks below we have denoted what the check generates.

- Branch Hygiene:
  - [WARNING] Branch names
  - [INFO] Commit information for live branches.
- File Hygiene:
  - [ERROR] Unnecessary and cache file (such as .DS_Store or pycache files)
- Notebook Files (\*.ipynb):
  - [ERROR] Cells per notebook < 10, lines per cell < 15 and 0 functions defined
  - [ERROR] Linting: PyLint, Black, Flake and iSort
- Python Files
  - [ERROR] All Code in Functions
  - [ERROR] All functions have docstrings
  - [ERROR] Code uses off-limit libraries (subprocess)
  - [ERROR] Linting: PyLint, Black, Flake and iSort

### Github actions

There is a Github action located [here](.github/workflows/error.badges.yml) that runs `cocoa` on pushes to the main branch. The action has an associated badge that can be displayed at the top of your repo to show passing or failing status. The badge code can be copied from the raw text of this readme.

To override the `--date` or `--branch` options run in the action, create an environment named "cocoa_standards" in your repository, then create environment variables called `BRANCH_NAME` and `REVIEW_AFTER_DATE`.