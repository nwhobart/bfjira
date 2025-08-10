import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from bfjira.main import main
from bfjira import __version__


# Mocks for external dependencies
@pytest.fixture
def mock_deps(mocker):
    # Mock environment variables
    mocker.patch.dict(
        os.environ,
        {
            "JIRA_SERVER": "https://jira.example.com",
            "JIRA_EMAIL": "test@example.com",
            "JIRA_API_TOKEN": "dummy-token",
            "JIRA_TICKET_PREFIX": "TEST",
        },
    )

    mock_repo = MagicMock()
    mock_jira = MagicMock()
    mocker.patch("bfjira.main.Repo", return_value=mock_repo)
    mocker.patch("bfjira.main.get_client", return_value=mock_jira)
    mocker.patch("bfjira.main.branch_name", return_value="feat/TKT-123-summary")
    mock_create_branch = mocker.patch("bfjira.main.create_branch")
    mock_transition = mocker.patch("bfjira.main.transition_to_in_progress")
    mock_stash = mocker.patch("bfjira.main.stash_changes")
    mock_pop = mocker.patch("bfjira.main.pop_stash")
    mock_to_git_root = mocker.patch("bfjira.main.to_git_root")
    mock_sys_exit = mocker.patch("sys.exit")
    mock_input = mocker.patch("builtins.input")

    # Make sys.exit raise an exception we can catch
    mock_sys_exit.side_effect = SystemExit

    return {
        "repo": mock_repo,
        "jira": mock_jira,
        "create_branch": mock_create_branch,
        "transition": mock_transition,
        "stash": mock_stash,
        "pop": mock_pop,
        "sys_exit": mock_sys_exit,
        "input": mock_input,
        "to_git_root": mock_to_git_root,
    }


def test_main_clean_repo(mock_deps):
    """Test main execution path with a clean repository."""
    mock_deps["repo"].is_dirty.return_value = False

    with patch.object(sys, "argv", ["bfjira", "-t", "TKT-123"]):
        main()

    mock_deps["to_git_root"].assert_called_once()
    mock_deps["repo"].is_dirty.assert_called_once_with(untracked_files=True)
    mock_deps["stash"].assert_not_called()
    mock_deps["create_branch"].assert_called_once_with("feat/TKT-123-summary", True)
    mock_deps["transition"].assert_called_once()
    mock_deps["pop"].assert_not_called()
    mock_deps["sys_exit"].assert_not_called()


def test_main_dirty_repo_stash_yes(mock_deps):
    """Test main execution with a dirty repo, user chooses to stash."""
    mock_deps["repo"].is_dirty.return_value = True
    mock_deps["input"].return_value = "y"
    mock_deps["stash"].return_value = True  # Stash succeeds

    with patch.object(sys, "argv", ["bfjira", "-t", "TKT-123"]):
        main()

    mock_deps["to_git_root"].assert_called_once()
    mock_deps["repo"].is_dirty.assert_called_once_with(untracked_files=True)
    mock_deps["input"].assert_called_once()
    mock_deps["stash"].assert_called_once()
    mock_deps["create_branch"].assert_called_once_with("feat/TKT-123-summary", True)
    mock_deps["transition"].assert_called_once()
    mock_deps["pop"].assert_called_once()  # Should pop after success
    mock_deps["sys_exit"].assert_not_called()


def test_main_dirty_repo_stash_no(mock_deps):
    """Test main execution with a dirty repo, user chooses not to stash."""
    mock_deps["repo"].is_dirty.return_value = True
    mock_deps["input"].return_value = "n"

    with patch.object(sys, "argv", ["bfjira", "-t", "TKT-123"]):
        with pytest.raises(SystemExit):
            main()

    mock_deps["to_git_root"].assert_called_once()
    mock_deps["repo"].is_dirty.assert_called_once_with(untracked_files=True)
    mock_deps["input"].assert_called_once()
    mock_deps["stash"].assert_not_called()
    mock_deps["create_branch"].assert_not_called()
    mock_deps["transition"].assert_not_called()
    mock_deps["pop"].assert_not_called()
    mock_deps["sys_exit"].assert_called_once_with(0)


def test_main_dirty_repo_stash_fail(mock_deps):
    """Test main execution with a dirty repo, stash operation fails."""
    mock_deps["repo"].is_dirty.return_value = True
    mock_deps["input"].return_value = "y"
    mock_deps["stash"].return_value = False  # Stash fails

    with patch.object(sys, "argv", ["bfjira", "-t", "TKT-123"]):
        with pytest.raises(SystemExit):
            main()

    mock_deps["to_git_root"].assert_called_once()
    mock_deps["repo"].is_dirty.assert_called_once_with(untracked_files=True)
    mock_deps["input"].assert_called_once()
    mock_deps["stash"].assert_called_once()
    mock_deps["create_branch"].assert_not_called()
    mock_deps["transition"].assert_not_called()
    mock_deps["pop"].assert_not_called()
    mock_deps["sys_exit"].assert_called_once_with(1)


def test_main_pop_stash_on_create_branch_error(mock_deps):
    """Test that stash is popped even if create_branch fails."""
    mock_deps["repo"].is_dirty.return_value = True
    mock_deps["input"].return_value = "y"
    mock_deps["stash"].return_value = True
    mock_deps["create_branch"].side_effect = Exception("Git error")

    with patch.object(sys, "argv", ["bfjira", "-t", "TKT-123"]):
        # We expect main() to raise the exception from create_branch
        with pytest.raises(Exception, match="Git error"):
            main()

    mock_deps["to_git_root"].assert_called_once()
    mock_deps["repo"].is_dirty.assert_called_once_with(untracked_files=True)
    mock_deps["input"].assert_called_once()
    mock_deps["stash"].assert_called_once()
    mock_deps["create_branch"].assert_called_once()
    mock_deps["transition"].assert_not_called()  # Should not be called if create fails
    mock_deps["pop"].assert_called_once()  # Should still pop
    mock_deps["sys_exit"].assert_not_called()  # Exception raised instead


# Add more tests as needed, e.g., for --no-progress, --no-upstream flags affecting mocks


def test_main_version_flag(capsys):
    """Ensure --version prints version and exits."""
    with patch.object(sys, "argv", ["bfjira", "--version"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out
