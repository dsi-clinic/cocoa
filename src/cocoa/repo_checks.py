from cocoa.git import get_remote_branches_info


def check_branch_names(repo_path):
    """
    Check for branches other than 'main' and 'dev' in the repository.

    Args:
        repo_path (str): The path to the repository.

    Returns:
        list: A list of warnings regarding branch names.
    """

    branches_info = get_remote_branches_info(repo_path)
    warnings = []

    for branch_info in branches_info:
        # Assuming branch_info is a list where the first item is the branch name
        # Extracts branch name after 'origin/'
        branch_name = branch_info[0].split('/')[-1]
        if branch_name not in ['main', 'dev']:
            warnings.append(
                f"Warning: Found non-standard branch '{branch_name}' in repository.")

    return warnings
