import os
import sys

from cocoa.utils import get_remote_branches_info, is_git_repo, walk_and_process


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
