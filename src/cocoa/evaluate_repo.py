"""Main entry point for evaluating a repo"""

import argparse
import os
import shutil
from pathlib import Path

from termcolor import cprint

from cocoa.config import DEFAULT_CONFIG, load_config
from cocoa.constants import PREAMBLE_TEXT
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


def walk_and_process(dir_path: str, config: dict, verbose: bool = False) -> None:
    """Walk through directory and process all python and jupyter notebook files."""
    paths_to_flag = ["__pycache__", "DS_Store", "ipynb_checkpoints"]
    cprint(
        f"Currently analyzing branch {get_current_branch(dir_path)}",
        color="green",
    )

    if config["start_date"]:
        files_to_process = files_after_date(dir_path, config["start_date"])
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
                    analyze_notebook(file_path, config, verbose)
                elif file_path.endswith(".py"):
                    analyze_python_file(file_path, config, verbose)


def analyze_notebook(file_path: str, config: dict, verbose: bool) -> None:
    """Analyze a notebook"""
    num_cells, num_lines, num_functions, max_lines_in_cell = process_notebook(file_path)

    ruff_results = run_ruff_and_capture_output(
        file_path, config["ruff_select"], config["ruff_ignore"]
    )
    ruff_results = process_ruff_results(ruff_results)

    if (
        len(ruff_results) > 0
        or num_cells > config["max_cells_per_notebook"]
        or max_lines_in_cell > config["max_lines_per_cell"]
        or num_functions > config["max_functions_per_notebook"]
    ):
        print(f"Analyzing {file_path}:")
        if len(ruff_results) > 0:
            print_results("ruff", ruff_results, verbose=verbose)

        if num_cells > config["max_cells_per_notebook"]:
            print(f"\tMax number of cells exceeded: {num_cells}")
        if max_lines_in_cell > config["max_lines_per_cell"]:
            print(f"\tMax number of lines per cell exceeded: {max_lines_in_cell}")
        if num_functions > config["max_functions_per_notebook"]:
            print(f"\tFunction definitions detected: {num_functions}")

        print("-" * 80)


def analyze_python_file(file_path: str, config: dict, verbose: bool) -> None:
    """Analyze a Python file"""
    contains_subprocess = code_contains_subprocess(file_path)
    code_in_functions = is_code_in_functions_or_main(file_path)
    ruff_results = run_ruff_and_capture_output(
        file_path, config["ruff_select"], config["ruff_ignore"]
    )
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
    config: dict,
) -> None:
    """Runs the repo evaluation."""
    cprint(PREAMBLE_TEXT, color="green")
    if Path(path_or_url).is_dir():
        if not is_git_repo(path_or_url):
            print(f"Error: {path_or_url} is not a Git repository.")
            exit(1)

        repo_path_obj = Path(path_or_url)
        config = load_config(repo_path_obj)
        switch_branches(path_or_url, config["branch_name"])

        check_branch_names(repo_path_obj)
        if config["branchinfo"]:
            get_remote_branches_info(repo_path_obj)

        walk_and_process(
            repo_path_obj,
            config=config,
        )

    elif is_git_remote_repo(path_or_url):
        repo_path = clone_repo(path_or_url)
        repo_path_obj = Path(repo_path)
        config = load_config(repo_path_obj)
        evaluate_repo(
            repo_path,
            config=config,
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

    # arguments added to parser based on DEFAULT_CONFIG in config.py
    for setting_name, setting_info in DEFAULT_CONFIG.items():
        # remove defaults. Since CLI overrides pyproject.toml, which overrides defaults,
        # we don't want to set defaults here.
        setting_info_no_default = {
            k: v for k, v in setting_info.items() if k != "default"
        }
        parser.add_argument(
            f"--{setting_name.replace('_', '-')}",
            **setting_info_no_default,
        )
    args = parser.parse_args()
    config = load_config(args.repo)
    for arg_name, arg_value in vars(args).items():
        if arg_value is not None:
            config[arg_name.replace("-", "_")] = arg_value

    dir_path = args.repo
    print(config)
    evaluate_repo(dir_path, config)


if __name__ == "__main__":
    main()
