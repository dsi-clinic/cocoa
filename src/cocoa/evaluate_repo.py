"""
Main entry point for complete evaluation of a python codebase in git
"""

import argparse
import os

from termcolor import cprint

from cocoa.constants import (
    MAX_CELLS_PER_NOTEBOOK,
    MAX_FUNCTIONS_PER_NOTEBOOK,
    MAX_LINES_PER_CELL,
)
from cocoa.linting import (
    black_python_file,
    code_contains_subprocess,
    functions_without_docstrings,
    get_pylint_warnings,
    is_code_in_functions_or_main,
    pyflakes_notebook,
    pyflakes_python_file,
)
from cocoa.notebooks import process_notebook
from cocoa.repo import (
    check_branch_names,
    clone_repo,
    files_after_date,
    get_current_branch,
    get_remote_branches_info,
    is_git_remote_repo,
    is_git_repo,
)


def walk_and_process(
    dir_path, no_filter_flag, lint_flag, start_date=None, verbose=False
):
    """
    Walk through directory and process all python and jupyter notebook files.
    """
    paths_to_flag = ["__pycache__", "DS_Store", "ipynb_checkpoints"]
    cprint(
        f"Currently analyzing branch {get_current_branch(dir_path)}",
        color="green",
    )

    if start_date:
        files_to_process = files_after_date(dir_path, start_date)
    else:
        files_to_process = [
            os.path.join(root, f)
            for root, _, files in os.walk(dir_path)
            for f in files
            if not any(x in os.path.join(root, f) for x in paths_to_flag)
        ]

    for file_path in files_to_process:
        if os.path.exists(file_path):
            if file_path.endswith(".ipynb") or file_path.endswith(".py"):
                if file_path.endswith(".ipynb"):
                    analyze_notebook(file_path, no_filter_flag, verbose)
                elif file_path.endswith(".py"):
                    analyze_python_file(file_path, lint_flag, verbose)


def analyze_notebook(file_path, no_filter_flag, verbose):
    """Analyze a notebook"""
    num_cells, num_lines, num_functions, max_lines_in_cell = process_notebook(
        file_path
    )
    pyflake_results = pyflakes_notebook(file_path)

    if (
        pyflake_results
        or num_cells > MAX_CELLS_PER_NOTEBOOK
        or max_lines_in_cell > MAX_LINES_PER_CELL
        or num_functions > MAX_FUNCTIONS_PER_NOTEBOOK
    ):
        print(f"Analyzing {file_path}:")
        if pyflake_results:
            print_results("PyFlakes", pyflake_results, verbose=verbose)

        if num_cells > MAX_CELLS_PER_NOTEBOOK:
            print(f"\tMax number of cells exceeded: {num_cells}")
        if max_lines_in_cell > MAX_LINES_PER_CELL:
            print(
                f"\tMax number of lines per cell exceeded: {max_lines_in_cell}"
            )
        if num_functions > MAX_FUNCTIONS_PER_NOTEBOOK:
            print(f"\tFunction definitions detected: {num_functions}")

        print("-" * 80)


def analyze_python_file(file_path, lint_flag, verbose):
    """Analyze a Python file"""
    pyflake_results = pyflakes_python_file(file_path)
    black_results = black_python_file(file_path)
    functions_no_docstrings = functions_without_docstrings(file_path)
    contains_subprocess = code_contains_subprocess(file_path)
    code_in_functions = is_code_in_functions_or_main(file_path)
    pylint_warnings = get_pylint_warnings(file_path)

    if (
        (lint_flag and pylint_warnings)
        or pyflake_results
        or black_results
        or functions_no_docstrings
        or contains_subprocess
        or not code_in_functions
    ):
        print(f"Analyzing {file_path}:")

        if pyflake_results:
            print_results("PyFlakes", pyflake_results, verbose=verbose)
        if black_results:
            print(f"\tBlack found {len(black_results)} issues")
        if functions_no_docstrings:
            print(
                "\tFunctions without docstrings detected:",
                functions_no_docstrings,
            )
        if contains_subprocess:
            print("\tSubprocess usage detected.")
        if not code_in_functions:
            print("\tCode outside functions or main block detected.")
        if lint_flag:
            print_results("Pylint", pylint_warnings, verbose=verbose)
        print("-" * 80)


def print_results(tool_name, results, verbose=False):
    """Print results from pylint or pyflake"""
    if results:
        if verbose:
            print(f"\t{tool_name} found {len(results)} issues:")
            for result in results:
                print(f"\t  {result}")
        else:
            print(f"\t{tool_name} found {len(results)} issues:")
            for result in results[:5]:
                print(f"\t  {result}")
            if len(results) > 5:
                print(f"\t  ...and {len(results) - 5} more issues.")


def evaluate_repo(path_or_url, lint_flag, start_date=None, verbose=False):
    """
    This is the entry point to running the automated code review.
    """

    if os.path.isdir(path_or_url):
        if not is_git_repo(path_or_url):
            print(f"Error: {path_or_url} is not a Git repository.")
            exit(1)

        check_branch_names(path_or_url)
        get_remote_branches_info(path_or_url)
        walk_and_process(
            path_or_url,
            None,
            lint_flag=lint_flag,
            start_date=start_date,
            verbose=verbose,
        )
    elif is_git_remote_repo(path_or_url):
        repo_path = clone_repo(path_or_url)
        evaluate_repo(
            repo_path,
            lint_flag=lint_flag,
            start_date=start_date,
            verbose=verbose,
        )
    else:
        print(f"Error: {path_or_url} is not a Git repository URL.")
        exit(1)
    return 0


def main():
    parser = argparse.ArgumentParser(description="COCOA CLI")

    parser.add_argument("repo", help="Path to a repository root directory")
    parser.add_argument("--lint", help="Run linting", action="store_true")
    parser.add_argument(
        "--verbose", help="Print all results", action="store_true"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Start date in YYYY-MM-DD format to filter files by commit date",
        type=str,
    )

    args = parser.parse_args()

    dir_path = args.repo
    lint_flag = args.lint
    start_date = args.date
    verbose = args.verbose

    evaluate_repo(dir_path, lint_flag, start_date, verbose)


if __name__ == "__main__":
    main()
