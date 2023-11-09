# BFJira - Branch Management with JIRA Integration

BFJira is a command-line utility that simplifies the process of creating Git branches based on JIRA ticket information. It ensures that branch names are consistent and informative by incorporating the issue type and summary from the JIRA ticket.

## Installation

The recommended way to install BFJira is via `pip` from PyPI:

```bash
pip install bfjira
```

Make sure you have `pip` installed and are using a virtual environment if necessary.

## Usage

To use BFJira, you must have the following environment variables set:

- `JIRA_SERVER`: Your JIRA server URL.
- `JIRA_EMAIL`: The email address associated with your JIRA account.
- `JIRA_API_TOKEN`: Your JIRA API token.

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

  If you only have the ticket number, BFJira will use the default prefix ("SRE" or whatever is set in `JIRA_TICKET_PREFIX`):

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

## Contributing

Contributions to BFJira are welcome! Please read the contributing guidelines before submitting pull requests.

## License

BFJira is released under the GNU General Public License. See the [LICENSE](LICENSE) file for more details.
