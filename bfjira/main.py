#!/usr/bin/env python3

import argparse
import os
import sys
from bfjira.jira_utils import get_client, branch_name, transition_to_in_progress
from bfjira.git_utils import to_git_root, create_branch
from bfjira.log_config import setup_logging


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Interact with JIRA and Git for branch management"
    )
    parser.add_argument("--ticket", "-t", help="The JIRA ticket ID (e.g., SRE-1234).")
    parser.add_argument(
        "--no-upstream",
        action="store_true",
        help="Do not set upstream for the new branch",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--issue-type",
        help="Set the type of issue for the branch prefix, overrides default issue type detection",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Do not transition the ticket to 'In Progress'",
    )

    args = parser.parse_args()

    logger = setup_logging(verbose=args.verbose)

    if not args.ticket:
        logger.error("No ticket ID provided.")
        parser.print_help()
        sys.exit(1)

    # Load JIRA configuration from environment variables
    jira_server = os.getenv("JIRA_SERVER")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    jira_ticket_prefix = os.getenv("JIRA_TICKET_PREFIX", "SRE")

    if not all([jira_server, jira_email, jira_api_token]):
        logger.error(
            "JIRA_SERVER, JIRA_EMAIL, and JIRA_API_TOKEN environment variables must be set."
        )
        sys.exit(1)

    ticket_id = args.ticket
    if ticket_id.isnumeric():
        ticket_id = f"{jira_ticket_prefix}-{ticket_id}"

    # Initialize JIRA client
    jira = get_client(jira_server, jira_email, jira_api_token)

    # Generate branch name based on JIRA ticket
    generated_branch_name = branch_name(jira, ticket_id, args.issue_type)

    # Perform Git operations
    to_git_root()
    create_branch(generated_branch_name, not args.no_upstream)

    # Transition JIRA ticket to 'In Progress'
    if not args.no_progress:
        transition_to_in_progress(jira, ticket_id)
    else:
        logger.info(
            f"Ticket {ticket_id} not transitioned to 'In Progress' as per user request."
        )


if __name__ == "__main__":
    main()
