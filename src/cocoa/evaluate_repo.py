import os
import sys

from termcolor import cprint

from cocoa.constants import (
    MAX_CELLS_PER_NOTEBOOK,
    MAX_FUNCTIONS_PER_NOTEBOOK,
    MAX_LINES_PER_CELL,
)
from cocoa.git import get_current_branch, get_remote_branches_info, is_git_repo
from cocoa.linting import (
    black_python_file,
    get_pylint_warnings,
    pyflakes_notebook,
    pyflakes_python_file,
)
from cocoa.notebooks import process_notebook


def walk_and_process(dir_path, no_filter_flag, lint_flag):
    """
    Walk through directory and process all python and jupyter notebook files.
    """
    paths_to_flag = ["__pycache__", "DS_Store", "ipynb_checkpoints"]
    cprint(
        f"Currently analyzing branch {get_current_branch( dir_path)}",
        color="green",
    )
    pylint_warnings = []

    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)

            pyflake_results = []

            if file.endswith(".ipynb"):
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

            elif file.endswith(".py"):
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

            if len(pyflake_results) > 0:
                print(*pyflake_results, sep="\n")

            if len([x for x in paths_to_flag if x in file]) > 0:
                print(
                    f"Warning: the file {file_path} should be \
                      filtered via gitignore."
                )

    return None


def main(argv=None) -> int:
    """
    This is the entry point to running the automated code review
    It should be called from inside the docker container
    """
    if argv is None:
        argv = sys.argv[1:]

    dir_path = argv[0]

    if not os.path.isdir(dir_path):
        print(f"Error: {dir_path} is not a valid directory.")
        exit(1)

    if not is_git_repo(dir_path):
        print(f"Error: {dir_path} is not a Git repository.")
        exit(1)

    if os.getenv("LINT") is not None and len(os.getenv("LINT")) > 0:
        lint_flag = True
    else:
        lint_flag = False

    get_remote_branches_info(dir_path)
    walk_and_process(dir_path, None, lint_flag=lint_flag)
    return 0
