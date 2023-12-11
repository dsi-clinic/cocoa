import json
import os

from termcolor import cprint

from cocoa.git import get_current_branch
from cocoa.linting import (
    black_python_file,
    get_pylint_warnings,
    pyflakes_notebook,
    pyflakes_python_file,
)


def count_functions(cell):
    """Count the number of functions defined in a Jupyter Notebook cell."""
    code = cell["source"]
    return len([1 for line in code if line.strip().startswith("def ")])


def process_notebook(file_path):
    """
    Process a Jupyter Notebook and count the cells, lines of code
    and functions.
    """
    with open(file_path, "r", encoding="utf-8") as f_handle:
        notebook = json.load(f_handle)
        cells = notebook["cells"]
        num_cells = len(cells)
        num_lines = 0
        num_functions = 0
        max_lines_in_cell = 0
        for cell in cells:
            if cell["cell_type"] == "code":
                lines_in_cell = len(
                    [1 for line in cell["source"] if line.strip()]
                )
                num_lines += lines_in_cell
                max_lines_in_cell = max(max_lines_in_cell, lines_in_cell)
                num_functions += count_functions(cell)
        return num_cells, num_lines, num_functions, max_lines_in_cell


def walk_and_process(dir_path, no_filter_flag, lint_flag):
    """
    Walk through directory and process all Jupyter Notebooks.
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
                    num_cells > 10
                    or max_lines_in_cell > 15
                    or num_functions > 0
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
