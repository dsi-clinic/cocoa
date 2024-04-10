# Clinic Opinionated Codebase Oversight and Analysis

This repository was developed in order to generate automated reports on how well codebases adhere to the [coding standards](https://github.com/dsi-clinic/coding-standards) of the University of Chicago's DSI [Clinic course](https://datascience.uchicago.edu/education/data-science-clinic/).

The goals of this codebase is to provide a quick and easy way to review code and to alert contributors where their code may be failing.

## Installation

```pip install cocoa```

To install the package from the local files, run the following command from the root of the repository:
```python3 -m pip install .```

### cocoa

This package contains a module `evaluate_repo` which runs code testing libraries against a repository. 

### How to run

Via command line: 
```bash
cocoa /path/to/repo
```

As a python script: 
```bash
python3 /src/cocoa/evaluate_repo.py /path/to/repo
```

A few important notes:

1. Make sure to `git pull` _before_ running this code.
1. This will get branch information for all branches.
1. This will only run the analysis (`pyflakes` on python files) for the code _in the current branch_. So if you run this while your current branch is `main` it will run on `main`.

If you want to do a full linting, then you can add the argument "--lint" to the command, such as:

```bash
cocoa /path/to/repo --lint
```