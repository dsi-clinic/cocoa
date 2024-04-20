from evaluate_repo import evaluate_repo
from repo import clone_repo


def process_repos(repo_urls):
    """
    Processes a list of Git repository URLs by cloning each repository, evaluating it,
    and collecting the results. Each repository is cloned using the `clone_repo`
    function, and then evaluated by calling the `evaluate_repo` function.

    Parameters:
    - repo_urls (list of str): A list of URLs for the Git repositories to be processed.

    Returns:
    - list of tuple: Each tuple contains the repository URL and the result of the
            evaluation.
                      If the repository could not be processed, the result is `None`.
    """
    results = []
    for repo_url in repo_urls:
        print(f"Processing {repo_url}")
        try:
            repo_path = clone_repo(repo_url)
            result = evaluate_repo(repo_path, lint_flag=True)
            results.append((repo_url, result))
        except Exception as e:
            print(f"Failed to process {repo_url}: {e}")
            results.append((repo_url, None))

    for repo, result in results:
        print(f"Repo: {repo}, Result: {result}")


if __name__ == "__main__":
    # Example list of repositories to process
    repos = [
        "https://github.com/dsi-clinic/2023-Autumn-Clinic-Fermi-CaloDiffusionPaper",
    ]
    process_repos(repos)
