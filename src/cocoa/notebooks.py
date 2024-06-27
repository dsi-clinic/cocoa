"""Utilities for evaluating the status and structure of Jupyter Notebooks"""

import json
from pathlib import Path


def count_functions(cell: dict) -> int:
    """Count the number of functions defined in a Jupyter Notebook cell."""
    code = cell["source"]
    return len([1 for line in code if line.strip().startswith("def ")])


def process_notebook(file_path: str) -> tuple[int, int, int, int]:
    """Process a Jupyter Notebook and count the cells, lines of code and functions.

    Args:
        file_path: path to the file to be processed
    """
    with Path(file_path).open(encoding="utf-8") as f_handle:
        notebook = json.load(f_handle)
        cells = notebook["cells"]
        num_cells = len(cells)
        num_lines = 0
        num_functions = 0
        max_lines_in_cell = 0
        for cell in cells:
            if cell["cell_type"] == "code":
                lines_in_cell = len([1 for line in cell["source"] if line.strip()])
                num_lines += lines_in_cell
                max_lines_in_cell = max(max_lines_in_cell, lines_in_cell)
                num_functions += count_functions(cell)
        return num_cells, num_lines, num_functions, max_lines_in_cell
