#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import sys
from git import Repo
from jira import JIRA
from jira.exceptions import JIRAError

# Set up logging
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


def change_to_git_root():
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], universal_newlines=True
        ).strip()
        os.chdir(git_root)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to find git repository root: {e}")
        sys.exit(1)


def sanitize_branch_name(name):
    return re.sub(r"[^a-zA-Z0-9-_]", "", name.replace(" ", "_"))


def get_transition_id_for_in_progress(jira, ticket_id):
    try:
        transitions = jira.transitions(ticket_id)
        for transition in transitions:
            if transition["name"].lower() == "in progress":
                return transition["id"]
        raise ValueError("Transition to 'In Progress' not found.")
    except JIRAError as e:
        logger.error(f"Error fetching transitions for ticket {ticket_id}: {e}")
        return None


def transition_jira_ticket_to_in_progress(jira, ticket_id, transition_id):
    try:
        jira.transition_issue(ticket_id, transition_id)
        logger.info(f"Ticket {ticket_id} moved to 'In Progress'.")
    except JIRAError as e:
        logger.error(f"Failed to move ticket {ticket_id} to 'In Progress': {e}")


def get_branch_name_based_on_jira_ticket(
    jira_server, jira_email, jira_api_token, ticket_id, issue_type_override=None
):
    if "-" not in ticket_id:
        logger.error("Ticket ID must include a prefix followed by a hyphen.")
        sys.exit(1)
    jira = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))
    ticket = jira.issue(ticket_id)
    issue_type_from_jira = ticket.fields.issuetype.name.lower()
    issue_type = issue_type_override if issue_type_override else issue_type_from_jira
    branch_prefix = (
        "feature"
        if issue_type == "story"
        else "fix"
        if issue_type == "bug"
        else issue_type  # Use the override as the prefix if provided
    )
    sanitized_summary = sanitize_branch_name(ticket.fields.summary)
    branch_name = f"{branch_prefix}/{ticket_id}-{sanitized_summary.lower()}"
    if len(branch_name) > 100:
        branch_name = branch_name[:100]
    return branch_name


def create_git_branch_and_set_upstream(branch_name, jira, ticket_id, set_upstream=True):
    repo = Repo()
    if repo.is_dirty():
        logger.info("Please commit your changes before creating a new branch.")
        return
    origin = repo.remotes.origin
    logger.info("Pulling the latest changes from the remote repository...")
    origin.pull()
    logger.info("Successfully pulled the latest changes.")
    logger.info(f"Creating new branch '{branch_name}'...")
    repo.create_head(branch_name)
    logger.info(f"Successfully created new branch '{branch_name}'.")
    logger.info(f"Checking out to the new branch '{branch_name}'...")
    repo.heads[branch_name].checkout()
    if set_upstream:
        logger.info(
            f"Pushing the new branch '{branch_name}' and setting the upstream..."
        )
        origin.push(branch_name, set_upstream=True)
        logger.info(
            f"Successfully pushed the new branch '{branch_name}' and set the upstream."
        )
    else:
        logger.info(f"Not setting upstream for '{branch_name}'.")

    # Transition JIRA ticket to 'In Progress' after branch creation
    transition_id = get_transition_id_for_in_progress(jira, ticket_id)
    if transition_id:
        transition_jira_ticket_to_in_progress(jira, ticket_id, transition_id)
    else:
        logger.warning(
            f"Could not find 'In Progress' transition for ticket {ticket_id}"
        )


def main():
    jira_server = os.environ.get("JIRA_SERVER")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_api_token = os.environ.get("JIRA_API_TOKEN")

    jira = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))

    parser = argparse.ArgumentParser(
        description="Interact with JIRA and Git for branch management."
    )
    parser.add_argument(
        "--ticket",
        "-t",
        help='The JIRA ticket ID (e.g., SRE-1234). If only a number is provided, the default prefix "SRE-" will be used.',
    )
    parser.add_argument(
        "--no-upstream",
        action="store_true",
        help="Do not set upstream for the new branch.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--issue-type",
        help="Set the type of issue for the branch prefix, overrides default issue type detection",
    )

    args = parser.parse_args()

    # Set logging level based on verbosity flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.ticket:
        parser.print_help()
        sys.exit(0)

    change_to_git_root()

    if not jira_email or not jira_api_token:
        logger.error("JIRA_EMAIL and JIRA_API_TOKEN environment variables must be set.")
        sys.exit(1)

    jira_ticket_prefix = os.getenv("JIRA_TICKET_PREFIX", "SRE")

    ticket_id = args.ticket
    if re.match(r"\d+", ticket_id):
        ticket_id = f"{jira_ticket_prefix}-{ticket_id}"

    if not re.match(r"([A-Z]+-)?\d+", ticket_id):
        logger.error("Invalid ticket ID format.")
        sys.exit(1)

    branch_name = get_branch_name_based_on_jira_ticket(
        jira_server, jira_email, jira_api_token, ticket_id, args.issue_type
    )
    create_git_branch_and_set_upstream(
        branch_name, jira, ticket_id, not args.no_upstream
    )


if __name__ == "__main__":
    main()
