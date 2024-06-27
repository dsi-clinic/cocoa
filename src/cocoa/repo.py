"""Utilities for evaluating the status and structure of a git repository"""

import tempfile
from datetime import datetime
from pathlib import Path

import git
import requests
from git import GitCommandError, Repo


def is_git_repo(repo_path: str) -> bool:
    """Return a boolean if the directory supplied is a git repo."""
    try:
        return git.Repo(repo_path).git_dir is not None
    except git.InvalidGitRepositoryError:
        raise Exception(f"Not a valid git repo: {repo_path}")  # noqa: B904


def get_remote_branches_info(repo_path: str, display: bool = True) -> list:
    """Returns the branch information from the remote repository."""
    repo = git.Repo(repo_path)
    remote_branches = repo.remote().refs

    branch_info = []
    for branch in remote_branches:
        if branch.remote_head == "HEAD":
            continue

        try:
            commits_diff = repo.git.rev_list(
                "--left-right", "--count", f"origin/main...{branch.name}"
            )
            num_ahead, num_behind = commits_diff.split("\t")
            branch_info.append([branch.name, num_ahead, num_behind])
        except git.GitCommandError:
            print("Error: Git command error occurred.")
    if display:
        for branch, behind, ahead in branch_info:
            print(f"Branch: {branch}")
            print(f"Commits behind main: {behind}")
            print(f"Commits ahead of main: {ahead}")
            print()

    return branch_info


def get_current_branch(repo_path: str) -> str:
    """Get the name of the current branch in a Git repository.

    Parameters:
        repo_path (str): The path to the Git repository.

    Returns:
        str: The name of the current branch, or None if an error occurs.

    Raises:
        git.InvalidGitRepositoryError: If the repository path is not a valid
        Git repo

        git.GitCommandError: If an error occurs while executing a Git command.
        Exception: For any other unexpected errors.
    """
    try:
        repo = git.Repo(repo_path)
        current_branch = repo.active_branch.name
        return current_branch
    except git.InvalidGitRepositoryError:
        print("Error: Not a valid Git repository.")
    except git.GitCommandError:
        print("Error: Git command error occurred.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def clone_repo(repo_url: str, dir_name: str = None) -> str:
    """Clones a Git repository into a directory or a temporary directory.

    Parameters:
    - repo_url (str): The URL of the repository to be cloned. This must not be empty.
    - dir_name (str, optional): The local directory name where the repository should
        be cloned. If None, a temporary directory is used.

    Returns:
    - str: The path to the cloned repository.
    """
    if not repo_url:
        raise ValueError("Repository URL must be provided.")

    try:
        # determine the directory path
        if dir_name:
            dir_path = dir_name
            if not Path(dir_path).exists():
                Path(dir_path).mkdir(parents=True)
            print(f"Using specified directory {dir_path} for cloning.")
        else:
            dir_path = tempfile.mkdtemp()
            print(f"Using temporary directory {dir_path} for cloning.")

        print(f"Cloning {repo_url} into {dir_path}")
        # repo_path = os.path.join(dir_path, repo_url.split("/")[-1])
        repo_path = str(Path(dir_path, repo_url.split("/")[-1]))

        # update but not clone if the dir existed
        if Path(repo_path).exists():
            print(f"The directory {repo_path} already exists. Fetching changes.")
            repo = Repo(repo_path)
            repo.remote().fetch()
        else:
            print(f"Cloning {repo_url} into {repo_path}")
            repo = Repo.clone_from(repo_url, repo_path)

        # get all branches
        repo.git.fetch("--all")

        return repo_path
    except GitCommandError as e:
        print(f"Error during git operation: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise


def check_branch_names(repo_path: str) -> list[str]:
    """Check for branches other than 'main' and 'dev' in the repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        list: A list of warnings regarding branch names.
    """
    branches_info = get_remote_branches_info(repo_path, False)
    warnings = []

    for branch_info in branches_info:
        # Assuming branch_info is a list where the first item is the branch name
        # Extracts branch name after 'origin/'
        branch_name = branch_info[0].split("/")[-1]
        if branch_name not in ["main", "dev"]:
            warnings.append(
                f"Warning: Found non-standard branch '{branch_name}' in repository."
            )

    for warning in warnings:
        print(warning)
    return warnings


def files_after_date(repo_path: str, start_date: str) -> list[str]:
    """Returns a list of files that have been committed after a specified start date.

    Args:
        repo_path (str): Path to the Git repository.
        start_date (str): Start date in 'YYYY-MM-DD' format.

    Returns:
        List[str]: A list of file paths committed after the start date.
    """
    repo = git.Repo(repo_path)
    since_date = datetime.strptime(start_date, "%Y-%m-%d")
    files_modified = []

    for commit in repo.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date)
        if commit_date > since_date:
            for entry in commit.stats.files.keys():
                file_path = str(Path(repo.working_dir, entry))
                if file_path not in files_modified:
                    files_modified.append(file_path)
    return files_modified


def is_git_remote_repo(url: str) -> bool:
    """Check if a url is a git remote"""
    # Normalize the URL by ensuring it ends with '.git'
    if not url.endswith(".git"):
        url += ".git"

    try:
        response = requests.get(url, timeout=10)
        if response.ok:
            return True
    except requests.RequestException as e:
        print(f"Failed to access {url}: {e}")

    return False


def switch_branches(repo_path: str, target_branch: str) -> None:
    """Switch branches in a repository"""
    repo = git.Repo(repo_path)
    # Fetch all branches from remote
    repo.git.fetch()

    # Check if the target branch exists locally or remotely
    if target_branch in repo.heads:
        # Checkout the local branch
        repo.git.checkout(target_branch)
        print(f"Switched to local branch: {target_branch}")
    elif target_branch in repo.remotes.origin.refs:
        # Checkout the remote branch
        repo.git.checkout("-b", target_branch, f"origin/{target_branch}")
        print(f"Switched to remote branch: {target_branch}")
    else:
        print(f"Branch '{target_branch}' does not exist locally or remotely.")
