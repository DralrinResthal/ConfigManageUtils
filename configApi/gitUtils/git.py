from dotenv import load_dotenv
from github import Github
from git import Actor
from shutil import rmtree
from datetime import datetime
import traceback
import git
import sys
import os, string, random
import logging

load_dotenv()

token = os.getenv("ACCESS_TOKEN")
git_log = logging.getLogger("git_log")
err_log = logging.getLogger("error_log")


def dirname_exists(dirname: str) -> bool:
    """Check if the dirname specified exists.
    If so, delete that dirname so that the repository can be cloned properly

    dirname: String name of directory

    returns True if directory exists and cannot be removed,
    False if directory does not exist or exists and was removed.
    """
    if os.path.exists(dirname):
        try:
            rmtree(dirname, ignore_errors=True)
            git_log.info(
                f"{dirname} previously existed and has now been removed."
            )
            return False
        except OSError as e:
            err_log.warning(f"Error removing directory {dirname}")
            err_log.warning(e)
            git_log.warning(
                f"{dirname} exists and CANNOT be removed. Please see error.log for more details."
            )
            return True
    else:
        return False


def clone(uri: str, target: str) -> None:
    """Clone a private repo with access token

    uri: Repository uri less "https://"
    target: local directory name target; what will you call local?

    example uri "github.com/DralrinResthal/ScanSlated-Portal.git"

    """
    token = os.getenv("ACCESS_TOKEN")
    remote = f"https://{token}:x-oauth-basic@github.com/{uri}.git"
    try:
        git.Repo.clone_from(remote, target)
        git_log.info(f"Repository '{uri}' has been cloned to {target}")

    except:
        msg = f"Unable to clone repository {uri}. {traceback.format_exc()}"
        err_log.warning(msg)


def reset_to_main(repo: str):
    """Switches repo to main branch

    repo: String name of local repo
    """
    repo = git.Repo(repo)
    try:
        repo.heads.main.checkout()
    except:
        err_log.warning("Placeholder, update this later")


def new_branch(repo: str) -> None:
    """Creates and switches to a new branch

    repo: Local repo name
    branch: Name of new branch
    """
    chars = string.ascii_letters + string.digits
    length = 20
    repo = git.Repo(repo)
    new_branch_name = "".join(random.choice(chars) for i in range(length))
    try:
        new_branch = repo.create_head(new_branch_name)
    except:
        return sys.exc_info()

    new_branch.checkout()

    return new_branch_name


def add_commit(
    repo: str, changes: list, message: str, name: str, email: str
) -> None:
    """Stage all changes and commit them in one single step.

    repo: local name of repository
    changes: List of all filenames to stage
    message: Commit message string
    name: Author name string
    email: Author email string
    """
    # Initialize repository
    repo = git.Repo(repo)
    # Stage chagnes
    repo.index.add(changes)
    author = Actor(name, email)
    committer = Actor("Config Manager", "configmgmt@example.com")
    # Commit staged changes
    repo.index.commit(message, author=author, committer=committer)
    # Push to remote
    repo.git.push("--set-upstream", repo.remote("origin"), repo.head.ref)


def pull(repo: str) -> None:
    """Pull (update) git repo

    repo: local name of repository
    """
    repo = git.Repo(repo)
    origin = repo.remotes.origin
    origin.pull()


def create_pr(uri: str, dir: str, user: str, branch_name: str) -> None:
    """Create a new pull request, always from <branch> to <main>

    uri: Git repo uri, User/Repository
    dir: Local directory name
    user: Username to include in PR
    branch_name: Branch to create PR from
    """
    # Generating variables
    now = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    title = f"Config Change - {now}"
    msg = f"Created by: {user} at {now}"

    # Move into local directory
    os.chdir(dir)

    # Instanciate Github using current local directory
    g = Github(os.getenv("ACCESS_TOKEN"))

    # Instanciate repository in current local directory
    repo = g.get_repo(uri)

    # Create the PR
    repo.create_pull(title=title, body=msg, head=branch_name, base="main")

    # Moved back out of current local directory
    os.chdir("../")
