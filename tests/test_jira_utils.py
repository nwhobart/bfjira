import pytest
from unittest.mock import Mock, patch, MagicMock
from bfjira.jira_utils import get_client, branch_name, transition_to_in_progress


def test_get_client():
    with patch("jira.JIRA") as mock_jira:
        mock_jira.return_value = "mock_client"
        client = get_client("https://server", "email", "token")
        assert client == "mock_client"
        mock_jira.assert_called_once_with(
            server="https://server", basic_auth=("email", "token")
        )


def test_branch_name():
    mock_jira = Mock()
    mock_issue = Mock()
    mock_issue.fields.issuetype.name = "Story"
    mock_issue.fields.summary = "Test Summary"
    mock_jira.issue.return_value = mock_issue

    result = branch_name(mock_jira, "TEST-123")
    assert result.startswith("feature/TEST-123-test_summary")


def test_transition_to_in_progress():
    mock_jira = Mock()
    mock_transition = MagicMock()
    mock_transition.__getitem__.return_value = "In Progress"
    mock_transition.id = "123"
    mock_jira.transitions.return_value = [mock_transition]

    transition_to_in_progress(mock_jira, "TEST-123")
    mock_jira.transition_issue.assert_called_once_with("TEST-123", "123")
