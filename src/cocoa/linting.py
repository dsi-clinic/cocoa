""""
Utility Functions for evaluating the status and structure of python code
"""

import ast
import difflib
import os
import tempfile
from io import StringIO

import black
from nbconvert import PythonExporter
from pyflakes.api import checkPath
from pyflakes.reporter import Reporter
from pylint.lint import Run
from pylint.reporters.text import TextReporter


def convert_temp_names_to_originals(
    errors_and_warnings: list, original_path: str
):
    """In a list of errors ["<path>: <error>"], converts path to original_path

    When Jupyter Notebooks are converted to python temp files and run throughj
    pyflakes, the reported errors are for the temp files. This function converts
    them back to be more descriptive

    Args:
        errors_and_warnings: list of pyflakes errors and warnings of the format
            ["<path>: <error/warning>"]
        original_path: name of original jupyter notebook
    Returns: list with format ["<original_path>: <error/warning>"]
    """
    # assuming format of <path> is <path>:<line no>:<column no>:, we want first colon
    return [
        original_path + path_and_message[path_and_message.find(":") :]
        for path_and_message in errors_and_warnings
    ]


def pyflakes_notebook(path_to_notebook):
    """
    Run pyflakes on a Jupyter notebook.
    :param path_to_notebook: path to the notebook file.
    :return: list of warnings and errors from pyflakes.
    """
    try:
        # Convert notebook to Python script
        exporter = PythonExporter()
        script, _ = exporter.from_filename(path_to_notebook)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".py"
        ) as temp:
            temp_name = temp.name
            temp.write(script)

        errors_and_warnings = pyflakes_python_file(temp_name)
        reformatted_errors_and_warnings = convert_temp_names_to_originals(
            errors_and_warnings,
            path_to_notebook,
        )

        # Delete temporary file
        os.remove(temp_name)
        return reformatted_errors_and_warnings
    except Exception as e:
        print(f"An error occurred while running pyflakes: {e}")


def pyflakes_python_file(file_path):
    """
    Run a python file through pyflakes. returns the number of warnings raised.
    """
    # Prepare StringIO object for capturing pyflakes output
    error_stream = StringIO()
    warning_stream = StringIO()

    reporter = Reporter(warning_stream, error_stream)

    # Run pyflakes and capture output
    checkPath(file_path, reporter=reporter)

    # Get errors and warnings
    errors = [
        ":".join([file_path] + x.split(":")[1:])
        for x in error_stream.getvalue().splitlines()
    ]

    warnings = [
        ":".join([file_path] + x.split(":")[1:])
        for x in warning_stream.getvalue().splitlines()
    ]

    return errors + warnings


def get_pylint_warnings(filepath):
    """
    Run pylint on the specified file and return warnings,
    ignoring specific error codes.
    """
    # Define the error codes to ignore
    ignored_errors = {"E0401"}

    # Capture the output in a string buffer
    output = StringIO()
    reporter = TextReporter(output=output)

    try:
        # Run pylint with specified reporter and arguments
        Run([filepath], reporter=reporter, exit=False)

        # Retrieve pylint output from the buffer
        pylint_output = output.getvalue()
        warnings = []
        # Filter out the ignored errors
        for line in pylint_output.split("\n"):
            if not any(code in line for code in ignored_errors):
                warnings.append(line)
        return warnings[1:-5]
    except Exception as e:
        print(f"An error occurred while running pylint: {e}")

    finally:
        # Clean up the StringIO object
        output.close()


def black_python_file(file_path):
    """
    Runs black on a python file. Returns a list of diffs from
    the original file.
    """
    try:
        # Read the content of the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Use Black's API to format the code
        formatted_content = black.format_file_contents(
            content,
            fast=False,
            mode=black.FileMode(line_length=80),
        )

        # Compare original and formatted content
        diff = difflib.unified_diff(
            content.splitlines(),
            formatted_content.splitlines(),
            fromfile="original",
            tofile="formatted",
            lineterm="",
        )

        diff_list = list(diff)

        # diff_str = "\n".join(diff)
        return diff_list if len(diff_list) > 0 else None

    except black.NothingChanged:
        return None
    except Exception as e:
        return f"Unexpected error: {e}"


def is_code_in_functions_or_main(file_path):
    """
    Check if all code in the given Python script is within functions or the main block.

    Args:
        file_path (str): The path to the Python script.

    Returns:
        bool: True if all code is within functions or main block, False otherwise.
    """

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=file_path)

        # Assume code is properly encapsulated until found otherwise
        properly_encapsulated = True

        # Check each statement in the module
        for node in tree.body:
            # Ignore import statements
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue

            # Check for function or class definitions, main block, and module docstrings
            if not (
                isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
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


def functions_without_docstrings(file_path):
    """
    Identify all functions in a given Python file that do not have docstrings.

    Args:
        file_path (str): Path to the Python script.

    Returns:
        list: A list of names of functions that do not have docstrings.
    """

    try:
        with open(file_path, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read(), filename=file_path)

        no_docstrings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if first node in function body is a docstring
                if not (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Str, ast.Constant))
                ):
                    no_docstrings.append(node.name)
        return no_docstrings
    except IOError as e:
        print(f"Error opening or reading the file: {e}")
        return []


class SubprocessVisitor(ast.NodeVisitor):
    def __init__(self):
        self.found = False

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "subprocess":
                self.found = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == "subprocess":
            self.found = True
        self.generic_visit(node)


def code_contains_subprocess(filepath):
    """
    Check if code uses subprocess.

    Args:
        file_path (str): The path to the Python script.

    Returns:
        bool: True if code contains subprocess, False otherwise.
    """
    try:
        with open(filepath, "r") as file:
            # Read the content of the file
            file_content = file.read()
            # Parse the content into an AST
            tree = ast.parse(file_content)
            # Create an instance of the visitor and run it on the AST
            visitor = SubprocessVisitor()
            visitor.visit(tree)
            return visitor.found
    except IOError as e:
        print(f"Error opening or reading the file: {e}")
        return False
