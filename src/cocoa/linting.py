"""Utility Functions for evaluating the status and structure of python code"""

import ast
import re
import subprocess
from pathlib import Path


def run_ruff_and_capture_output(path: str) -> str:
    """Runs ruff as subprocess and return output as a string."""
    try:
        # Run the ruff command
        result = subprocess.run(["ruff", "check", path], capture_output=True, text=True)  # noqa

        # Combine stdout and stderr
        output = result.stdout + result.stderr

        return output
    except Exception as e:
        return str(e)


def find_first_match_index(lst: list, pattern: str) -> int:
    """Finds the first match in a list and returns the index."""
    regex = re.compile(pattern)
    for index, item in enumerate(lst):
        if regex.match(item):
            return index
    return -1  # Return -1 if no match is found


def process_ruff_results(results: list) -> list:
    """Process ruff results into a list of errors."""
    results = results.split("\n")
    fmi = find_first_match_index(results, r"Found \d+ error")  # noqa: Q000

    if fmi == -1:
        return []
    return results[:fmi]


def is_code_in_functions_or_main(file_path: str) -> bool:
    """Check if all code in the given Python script is within functions or the main block.

    Args:
        file_path (str): The path to the Python script.

    Returns:
        bool: True if all code is within functions or main block, False otherwise.
    """
    try:
        with Path(file_path).open(encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=file_path)

        # Assume code is properly encapsulated until found otherwise
        properly_encapsulated = True

        # Check each statement in the module
        for node in tree.body:
            # Ignore import statements
            if isinstance(node, ast.Import | ast.ImportFrom):
                continue

            # Check for function or class definitions, main block, and module docstrings
            if not (
                isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
                or (
                    isinstance(node, ast.If)
                    and isinstance(node.test, ast.Compare)
                    and isinstance(node.test.ops[0], ast.Eq)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"
                    and isinstance(node.test.comparators[0], ast.Constant)
                    and node.test.comparators[0].value == "__main__"
                )
                or isinstance(node.value, ast.Constant)
            ):
                # Found code that is not in a function/class def or the main block
                properly_encapsulated = False
                break

        return properly_encapsulated
    except SyntaxError:
        print(f"SyntaxError while parsing file {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


class SubprocessVisitor(ast.NodeVisitor):
    """Ast node visitor."""

    def __init__(self) -> None:
        """Create a new SubprocessVisitor"""
        self.found = False

    def visit_Import(self, node) -> None:  # noqa
        for alias in node.names:
            if alias.name == "subprocess":
                self.found = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):  # noqa
        if node.module == "subprocess":
            self.found = True
        self.generic_visit(node)


def code_contains_subprocess(filepath: str) -> bool:
    """Check if code uses subprocess.

    Args:
        filepath (str): The path to the Python script.

    Returns:
        bool: True if code contains subprocess, False otherwise.
    """
    try:
        with Path(filepath).open() as file:
            # Read the content of the file
            file_content = file.read()
            # Parse the content into an AST
            tree = ast.parse(file_content)
            # Create an instance of the visitor and run it on the AST
            visitor = SubprocessVisitor()
            visitor.visit(tree)
            return visitor.found
    except OSError as e:
        print(f"Error opening or reading the file: {e}")
        return False
