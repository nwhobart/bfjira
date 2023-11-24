![PyPI - Version](https://img.shields.io/pypi/v/bfjira)


# bfjira - Branch Management with JIRA Integration

bfjira (branch from Jira) is a command-line utility that simplifies the process of creating Git branches based on JIRA ticket information. It ensures that branch names are consistent and informative by incorporating the issue type and summary from the JIRA ticket.

## Installation

The recommended way to install bfjira is via `pip` from PyPI:

```bash
pip install bfjira
```

Make sure you have `pip` installed and are using a virtual environment if necessary.

## Usage

To use bfjira, you must have the following environment variables set:

- `JIRA_SERVER`: Your JIRA server URL.
- `JIRA_EMAIL`: The email address associated with your JIRA account.
- `JIRA_API_TOKEN`: Your JIRA API token.

Instructions for creating a Jira API token can be found [here](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)

Optionally, you can set the `JIRA_TICKET_PREFIX` environment variable to use a default prefix other than "SRE" for ticket IDs that are entered without a prefix.

### Basic Commands

- Show help message:

  ```bash
  bfjira --help
  ```

- Create a branch for a JIRA ticket:

  ```bash
  bfjira --ticket SRE-1234
  ```

  If you only have the ticket number, bfjira will use the default prefix ("SRE" or whatever is set in `JIRA_TICKET_PREFIX`):

  ```bash
  bfjira -t 1234
  ```

### Advanced Options

- Set a custom issue type for the branch:

  ```bash
  bfjira -t 1234 --issue-type hotfix
  ```

- Create a branch without setting the upstream:

  ```bash
  bfjira -t 1234 --no-upstream
  ```

- Increase output verbosity (useful for debugging):

  ```bash
  bfjira -t 1234 -v
  ```

- Optionally prevent transitioning the ticket to 'In Progress':

  By default, the script transitions the specified JIRA ticket to 'In Progress'. If you wish to create a branch for the ticket without changing its status, use the `--no-progress` flag. This is useful when you need to perform operations on the ticket without indicating that work has started.

  ```bash
  bfjira -t 1234 --no-progress
  ```

## Contributing

Contributions to bfjira are welcome! Please read the contributing guidelines before submitting pull requests.

## License

bfjira is released under the GNU General Public License. See the [LICENSE](LICENSE) file for more details.
