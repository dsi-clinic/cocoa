# Clinic Opinionated Codebase Oversight and Analysis

This repository was developed in order to generate automated reports on how well codebases adhere to the [coding standards](https://github.com/dsi-clinic/coding-standards) of the University of Chicago's DSI [Clinic course](https://datascience.uchicago.edu/education/data-science-clinic/).

The goals of this codebase is to provide a quick and easy way to review code and to alert contributors where their code may be failing.

## Installation

```pip install dsi-cocoa```

To install the package from the local files, run the following command from the root of the repository:
```bash
python3 -m pip install .
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

As a python script: 
```bash
python3 src/cocoa/evaluate_repo.py /path/to/repo
```

As a Python module:
```python
from cocoa.evaluate_repo import evaluate_repo

evaluate_repo('/path/to/repo', False)
```

A few important notes:

1. Make sure to `git pull` _before_ running this code.
1. This will get branch information for all branches.
1. This will only run the analysis (`pyflakes` on python files) for the code _in the current branch_. So if you run this while your current branch is `main` it will run on `main`.

#### Options
If you want to do linting on Python files, then you can add the argument "--lint" to the command:

```bash
cocoa /path/to/repo --lint
```

Results are truncated by default. To print all results, use the verbose option:

```bash
cocoa /path/to/repo --verbose
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
    - [ERROR] Unnecessary and cache file (such as .DS\_Store or pycache files)
- Notebook Files (*.ipynb):
    - [ERROR] Cells per notebook < 10, lines per cell < 15 and 0 functions defined
    - [ERROR] Linting: PyLint, Black, Flake and iSort
- Python Files
    - [ERROR] All Code in Functions
    - [ERROR] All functions have docstrings
    - [ERROR] Code uses off-limit libraries (subprocess)
    - [ERROR] Linting: PyLint, Black, Flake and iSort
    
### Github actions

For each of the ERRORS and WARNINGS above there is an associated github action that can be run to create a badge which we put in a table at the top of each clinic repo.

