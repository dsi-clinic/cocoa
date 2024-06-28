"""Main entry point for evaluating a repo"""

import argparse
import os
import shutil
from pathlib import Path

from termcolor import cprint

from cocoa.constants import (
    MAX_CELLS_PER_NOTEBOOK,
    MAX_FUNCTIONS_PER_NOTEBOOK,
    MAX_LINES_PER_CELL,
    PREAMBLE_TEXT,
)
from cocoa.linting import (
    code_contains_subprocess,
    is_code_in_functions_or_main,
    process_ruff_results,
    run_ruff_and_capture_output,
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
    switch_branches,
)


def walk_and_process(
    dir_path: str, start_date: str = None, verbose: bool = False
) -> None:
    """Walk through directory and process all python and jupyter notebook files."""
    paths_to_flag = ["__pycache__", "DS_Store", "ipynb_checkpoints"]
    cprint(
        f"Currently analyzing branch {get_current_branch(dir_path)}",
        color="green",
    )

    if start_date:
        files_to_process = files_after_date(dir_path, start_date)
    else:
        files_to_process = [
            str(Path(root, f))
            for root, _, files in os.walk(dir_path)
            for f in files
            if not any(x in str(Path(root, f)) for x in paths_to_flag)
        ]

    for file_path in files_to_process:
        if Path(file_path).exists():
            if file_path.endswith(".ipynb") or file_path.endswith(".py"):
                if file_path.endswith(".ipynb"):
                    analyze_notebook(file_path, verbose)
                elif file_path.endswith(".py"):
                    analyze_python_file(file_path, verbose)


def analyze_notebook(file_path: str, verbose: bool) -> None:
    """Analyze a notebook"""
    num_cells, num_lines, num_functions, max_lines_in_cell = process_notebook(file_path)

    ruff_results = run_ruff_and_capture_output(file_path)
    ruff_results = process_ruff_results(ruff_results)

    if (
        len(ruff_results) > 0
        or num_cells > MAX_CELLS_PER_NOTEBOOK
        or max_lines_in_cell > MAX_LINES_PER_CELL
        or num_functions > MAX_FUNCTIONS_PER_NOTEBOOK
    ):
        print(f"Analyzing {file_path}:")
        if len(ruff_results) > 0:
            print_results("ruff", ruff_results, verbose=verbose)

        if num_cells > MAX_CELLS_PER_NOTEBOOK:
            print(f"\tMax number of cells exceeded: {num_cells}")
        if max_lines_in_cell > MAX_LINES_PER_CELL:
            print(f"\tMax number of lines per cell exceeded: {max_lines_in_cell}")
        if num_functions > MAX_FUNCTIONS_PER_NOTEBOOK:
            print(f"\tFunction definitions detected: {num_functions}")

        print("-" * 80)


def analyze_python_file(file_path: str, verbose: bool) -> None:
    """Analyze a Python file"""
    contains_subprocess = code_contains_subprocess(file_path)
    code_in_functions = is_code_in_functions_or_main(file_path)
    ruff_results = run_ruff_and_capture_output(file_path)
    ruff_results = process_ruff_results(ruff_results)

    if contains_subprocess or len(ruff_results) > 0 or not code_in_functions:
        print(f"Analyzing {file_path}:")

        if len(ruff_results) > 0:
            print_results("ruff", ruff_results, verbose=verbose)

        if contains_subprocess:
            print("\tSubprocess usage detected.")
        if not code_in_functions:
            print("\tCode outside functions or main block detected.")
        print("-" * 80)


def print_results(tool_name: str, results: list, verbose: bool = False) -> None:
    """Print results from pylint or pyflake"""
    max_displayed = 5
    if results:
        if verbose:
            print(f"\t{tool_name} found {len(results)} issues:")
            for result in results:
                print(f"\t  {result}")
        else:
            print(f"\t{tool_name} found {len(results)} issues:")
            for result in results[:max_displayed]:
                print(f"\t  {result}")
            if len(results) > max_displayed:
                print(
                    f"\t  ...plus {len(results) - max_displayed} more. To see more details, use the --verbose flag."
                )


def evaluate_repo(
    path_or_url: str,
    start_date: str = None,
    verbose: bool = False,
    branchinfo: bool = False,
    branch_name: str = "main",
) -> None:
    """Runs the repo evaluation."""
    cprint(PREAMBLE_TEXT, color="green")
    if Path(path_or_url).is_dir():
        if not is_git_repo(path_or_url):
            print(f"Error: {path_or_url} is not a Git repository.")
            exit(1)

        switch_branches(path_or_url, branch_name)

        check_branch_names(path_or_url)
        if branchinfo:
            get_remote_branches_info(path_or_url)

        walk_and_process(
            path_or_url,
            start_date=start_date,
            verbose=verbose,
        )

    elif is_git_remote_repo(path_or_url):
        repo_path = clone_repo(path_or_url)
        evaluate_repo(
            repo_path,
            start_date=start_date,
            verbose=verbose,
        )
        shutil.rmtree(repo_path)
    else:
        print(f"Error: {path_or_url} is either private or not a git repository. 404.")
        exit(1)
    return 0


def main() -> None:
    """Main entry point for running the command line interface."""
    parser = argparse.ArgumentParser(description="COCOA CLI")

    parser.add_argument("repo", help="Path to a repository root directory")
    parser.add_argument("--verbose", help="Print all results", action="store_true")
    parser.add_argument(
        "--date",
        default=None,
        help="Start date in YYYY-MM-DD format to filter files by commit date",
        type=str,
    )
    parser.add_argument(
        "--branchinfo", help="Report branch information", action="store_true"
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Specify which branch to evaluate",
        type=str,
    )
    args = parser.parse_args()

    dir_path = args.repo
    start_date = args.date
    verbose = args.verbose
    branchinfo = args.branchinfo
    branch = args.branch

    evaluate_repo(dir_path, start_date, verbose, branchinfo, branch)


if __name__ == "__main__":
    main()
