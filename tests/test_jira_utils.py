"""Test suite for JIRA utilities."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from bfjira.jira_utils import branch_name, get_client, transition_to_in_progress


@patch("bfjira.jira_utils.JIRA")
def test_get_client(mock_jira_class):
    """Test JIRA client initialization."""
    mock_instance = Mock()
    mock_jira_class.return_value = mock_instance

    client = get_client("https://server", "email", "token")
    assert client == mock_instance
    mock_jira_class.assert_called_once_with(
        server="https://server", basic_auth=("email", "token")
    )


def test_branch_name():
    """Test branch name generation."""
    mock_jira = Mock()
    mock_issue = Mock()
    mock_issue.fields.issuetype.name = "Story"
    mock_issue.fields.summary = "Test Summary"
    mock_jira.issue.return_value = mock_issue

    result = branch_name(mock_jira, "TEST-123")
    assert result.startswith("feature/TEST-123-test_summary")


def test_transition_to_in_progress():
    """Test transitioning a ticket to In Progress."""
    mock_jira = Mock()
    mock_transition = {"id": "123", "name": "In Progress"}
    mock_jira.transitions.return_value = [mock_transition]

    transition_to_in_progress(mock_jira, "TEST-123")
    mock_jira.transition_issue.assert_called_once_with("TEST-123", "123")
