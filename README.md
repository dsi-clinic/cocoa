# Clinic Opinionated Codebase Oversight and Analysis

This repository was developed in order to generate automated reports on how well codebases adhere to the [coding standards](https://github.com/dsi-clinic/coding-standards) of the University of Chicago's DSI [Clinic course](https://datascience.uchicago.edu/education/data-science-clinic/).

The goals of this codebase is to provide a quick and easy way to review code and to alert contributors where their code may be failing.

## Installation

```pip install cocoa```

To install the package from the local files, run the following command from the root of the repository:
```bash
python3 -m pip install .
```

### cocoa

This package contains a module `evaluate_repo` which runs code testing libraries against a repository. There are multiple ways that we want to be able to run this repo:

1. We want to be able to clone `cocoa` and then use it as part of their process.
2. We want adminstrators to be able to give it a list of repos to generate reports on all repos.
3. (Eventually) We want it to be able to run as a github action _on the repo itself_.
4. (Eventually) We want to be able to have administrive repo that can run it on other repos.

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

If you want to do a full linting, then you can add the argument "--lint" to the command, such as:

```bash
cocoa /path/to/repo --lint
```
