from git import Repo
import os
import re
import subprocess
import sys
import logging

logger = logging.getLogger("bfjira")


def to_git_root():
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], universal_newlines=True
        ).strip()
        os.chdir(git_root)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to find git repository root: {e}")
        sys.exit(1)


def create_branch(branch_name, set_upstream=True):
    """
    Create a new Git branch and optionally set upstream.
    """
    try:
        repo = Repo(".")
        if repo.is_dirty():
            logger.error("Repository has uncommitted changes.")
            sys.exit(1)

        origin = repo.remotes.origin
        origin.pull()
        logger.info("Pulled the latest changes from the remote repository.")

        repo.create_head(branch_name).checkout()
        logger.info(f"Created and checked out new branch '{branch_name}'.")

        if set_upstream:
            origin.push(branch_name, set_upstream=True)
            logger.info(f"Pushed '{branch_name}' and set upstream.")
    except Exception as e:
        logger.error(f"Error while creating Git branch '{branch_name}': {e}")
        raise
