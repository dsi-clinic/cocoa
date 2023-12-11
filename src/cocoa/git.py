"""
Utilities for evaluating the status and structure of a git repository
"""
import git


def is_git_repo(repo_path):
    """
    Return a boolean if the directory supplied is a git repo.
    """
    return git.Repo(repo_path).git_dir is not None


def get_remote_branches_info(repo_path):
    """
    This function reutrns the branch information from the
    remote repository.
    """
    repo = git.Repo(repo_path)
    remote_branches = repo.remote().refs

    branch_info = []
    for branch in remote_branches:
        if branch.remote_head == "HEAD":
            continue

        commits_diff = repo.git.rev_list(
            "--left-right", "--count", f"origin/main...{branch.name}"
        )
        num_ahead, num_behind = commits_diff.split("\t")
        branch_info.append([branch.name, num_ahead, num_behind])

    for branch, behind, ahead in branch_info:
        print(f"Branch: {branch}")
        print(f"Commits behind main: {behind}")
        print(f"Commits ahead of main: {ahead}")
        print()

    return branch_info


def get_current_branch(repo_path):
    """
    Get the name of the current branch in a Git repository.

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
