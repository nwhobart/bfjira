#!/usr/bin/env python3

import os
import sys
import re
import logging
import subprocess
from git import Repo
from jira import JIRA

# Set up logging
logging.basicConfig(level=logging.INFO)


def show_help():
    help_text = """
Usage: bfjira [OPTIONS] [ARGUMENTS]

Options:
    help        Show this help message.

Arguments:
    [JIRA_ID]   ID of the JIRA ticket to use. If only a number is provided,
                the default prefix "SRE-" will be used (e.g., "1234" becomes "SRE-1234").
                Set the JIRA_TICKET_PREFIX environment variable to override the default prefix.

Examples:
    bfjira help
    bfjira 1234         # Assumes "SRE-1234"
    JIRA_TICKET_PREFIX=OPS bfjira 1234  # Uses "OPS-1234"
"""
    print(help_text.strip())


def change_to_git_root():
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], universal_newlines=True
        ).strip()
        os.chdir(git_root)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to find git repository root: {e}")
        sys.exit(1)


def sanitize_branch_name(name):
    return re.sub(r"[^a-zA-Z0-9-_]", "", name.replace(" ", "_"))


def get_branch_name_based_on_jira_ticket(
    jira_server, jira_email, jira_api_token, ticket_id
):
    if "-" not in ticket_id:
        logging.error("Ticket ID must include a prefix followed by a hyphen.")
        sys.exit(1)
    jira = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))
    ticket = jira.issue(ticket_id)
    issue_type = ticket.fields.issuetype.name.lower()
    branch_prefix = (
        "feature"
        if issue_type == "story"
        else "fix"
        if issue_type == "bug"
        else "issue"
    )
    sanitized_summary = sanitize_branch_name(ticket.fields.summary)
    branch_name = f"{branch_prefix}/{ticket_id}-{sanitized_summary.lower()}"
    if len(branch_name) > 100:
        branch_name = branch_name[:100]
    return branch_name


def create_git_branch_and_set_upstream(branch_name):
    repo = Repo()
    if repo.is_dirty():
        logging.info("Please commit your changes before creating a new branch.")
        return
    origin = repo.remotes.origin
    logging.info("Pulling the latest changes from the remote repository...")
    origin.pull()
    logging.info("Successfully pulled the latest changes.")
    logging.info(f"Creating new branch '{branch_name}'...")
    repo.create_head(branch_name)
    logging.info(f"Successfully created new branch '{branch_name}'.")
    logging.info(f"Checking out to the new branch '{branch_name}'...")
    repo.heads[branch_name].checkout()
    logging.info(f"Successfully checked out to '{branch_name}'.")
    logging.info(f"Pushing the new branch '{branch_name}' and setting the upstream...")
    origin.push(branch_name, set_upstream=True)
    logging.info(
        f"Successfully pushed the new branch '{branch_name}' and set the upstream."
    )


def main():
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1].lower() == "help"):
        show_help()
        sys.exit(0)

    change_to_git_root()

    jira_server = os.environ.get("JIRA_SERVER")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    if not jira_email or not jira_api_token:
        logging.error(
            "JIRA_EMAIL and JIRA_API_TOKEN environment variables must be set."
        )
        sys.exit(1)

    jira_ticket_prefix = os.getenv("JIRA_TICKET_PREFIX", "SRE")

    if len(sys.argv) == 2 and re.match(r"\d+", sys.argv[1]):
        ticket_id = f"{jira_ticket_prefix}-{sys.argv[1]}"
    elif len(sys.argv) == 2 and re.match(r"([A-Z]+-)?\d+", sys.argv[1]):
        ticket_id = sys.argv[1]
    else:
        ticket_input = input(
            f"Enter the JIRA ticket ID (e.g., '{jira_ticket_prefix}-1234' or just '1234' for default prefix): "
        )
        if re.match(r"\d+", ticket_input):
            ticket_id = f"{jira_ticket_prefix}-{ticket_input}"
        else:
            ticket_id = ticket_input

    if not re.match(r"([A-Z]+-)?\d+", ticket_id):
        logging.error("Invalid ticket ID format.")
        sys.exit(1)

    branch_name = get_branch_name_based_on_jira_ticket(
        jira_server, jira_email, jira_api_token, ticket_id
    )
    create_git_branch_and_set_upstream(branch_name)


if __name__ == "__main__":
    main()
