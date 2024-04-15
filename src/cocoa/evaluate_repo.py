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
    files_after_date,
    get_current_branch,
    get_remote_branches_info,
    is_git_repo,
)


def walk_and_process(dir_path, no_filter_flag, lint_flag, start_date=None):
    """
    Walk through directory and process all python and jupyter notebook files.
    """
    paths_to_flag = ["__pycache__", "DS_Store", "ipynb_checkpoints"]
    cprint(
        f"Currently analyzing branch {get_current_branch( dir_path)}",
        color="green",
    )

    # check for files after a specific data
    if start_date:
        files_to_process = files_after_date(dir_path, start_date)
    else:
        files_to_process = [
            os.path.join(root, f)
            for root, _, files in os.walk(dir_path)
            for f in files
        ]

    pylint_warnings = []

    for file_path in files_to_process:

        # Check if file path exists
        if os.path.exists(file_path):
            pyflake_results = []

            if file_path.endswith(".ipynb"):
                (
                    num_cells,
                    num_lines,
                    num_functions,
                    max_lines_in_cell,
                ) = process_notebook(file_path)

                if no_filter_flag or (
                    num_cells > MAX_CELLS_PER_NOTEBOOK
                    or max_lines_in_cell > MAX_LINES_PER_CELL
                    or num_functions > MAX_FUNCTIONS_PER_NOTEBOOK
                ):
                    print(f"File: {file_path}")
                    print(f"\tNumber of cells: {num_cells}")
                    print(f"\tLines of code: {num_lines}")
                    print(f"\tNumber of function definitions: {num_functions}")
                    print(f"\tMax lines in a cell: {max_lines_in_cell}")
                    print("-" * 40)

                pyflake_results = pyflakes_notebook(file_path)

            elif file_path.endswith(".py"):
                pyflake_results = pyflakes_python_file(file_path)
                black_results = black_python_file(file_path)
                if lint_flag:
                    pylint_warnings = get_pylint_warnings(file_path)
                    if len(pylint_warnings) > 0:
                        for warning in pylint_warnings:
                            print(f"{warning}")

                if black_results:
                    print(
                        f"There were {len(black_results)} changes "
                        f"on file {file_path}. Please run black."
                    )

                # check is_code_in_functions_or_main
                if not is_code_in_functions_or_main(file_path):
                    print(
                        f"Code outside functions or main block detected in {file_path}"
                    )

                # check if code uses subprocess
                if code_contains_subprocess(file_path):
                    print(f"Warning: subprocess usage detected in {file_path}")

                # check if functions have docstrings
                functions_no_docstrings = functions_without_docstrings(
                    file_path
                )

                if functions_no_docstrings:
                    print(
                        f"Following functions without docstrings"
                        f" detected in {file_path}:"
                        f"{functions_no_docstrings}"
                    )

            if len(pyflake_results) > 0:
                print(*pyflake_results, sep="\n")

            if len([x for x in paths_to_flag if x in file_path]) > 0:
                print(
                    f"Warning: the file {file_path} should be \
                      filtered via gitignore."
                )

    return None


def evaluate_repo(dir_path, lint_flag, start_date):
    """
    This is the entry point to running the automated code review
    It should be called from inside the docker container.
    """

    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a valid directory.")
        exit(1)

    if not is_git_repo(dir_path):
        print(f"Error: {dir_path} is not a Git repository.")
        exit(1)

    check_branch_names(dir_path)
    get_remote_branches_info(dir_path)
    walk_and_process(dir_path, None, lint_flag=lint_flag, start_date=start_date)
    return 0


def main():
    parser = argparse.ArgumentParser(description="COCOA CLI")

    parser.add_argument("repo", help="Path to a repository root directory")
    parser.add_argument("--lint", help="Lint option", action="store_true")
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

    evaluate_repo(dir_path, lint_flag, start_date)


if __name__ == "__main__":
    main()
