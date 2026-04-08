---
name: finance-cli
description: This skill should be used when the økonomi advisor needs to "check account balance", "list transactions", "export transactions", "check spending", "what did I spend last month", "fetch bank data from SpareBank 1", or interact with the finance CLI tool. Provides command syntax and usage reference.
user-invocable: false
---

# Finance CLI Reference

CLI tool for fetching personal financial data from SpareBank 1. Installed at `~/projects/finance-cli`.

## Output Modes

- **Default**: Human-readable table — use when displaying results to the user.
- **JSON**: Pass `--json` flag *before* the subcommand (e.g. `finance --json accounts list`) — use when parsing output programmatically or writing to files.
- **CSV**: The `export` command always outputs CSV — use when you need structured numeric data for calculations or analysis.

Errors go to stderr with exit code 1.

## Auth Prerequisites

Auth must be valid before any data command will work. If you get an auth error, run `finance auth status` to check. If the session has expired, the user must re-authenticate with `finance auth login` (interactive) or `finance auth login --headless` (server/SSH).

```bash
finance auth setup              # Enter client_id and client_secret (stored encrypted)
finance auth login              # Interactive BankID login (opens browser)
finance auth login --headless   # Headless: prints URL, you paste redirect back
finance auth status             # Check auth status
finance auth logout             # Clear all tokens
```

## Commands

### Accounts

```bash
finance accounts list                          # List all accounts
finance accounts get ACCOUNT_KEY               # Get single account details
finance accounts balance                       # Balance summary for all accounts
```

### Transactions

Use `list` for browsing/displaying transactions. Use `export` when you need data for calculation or structured analysis.

```bash
finance transactions list --account-key KEY                                    # List transactions
finance transactions list --account-key KEY --from 2026-01-01 --to 2026-03-01  # Date-filtered
finance transactions details TRANSACTION_ID                                    # Single transaction details
finance transactions export --account-key KEY --from 2026-01-01 --to 2026-03-01              # Export as CSV
finance transactions export --account-key KEY --from 2026-01-01 --to 2026-03-01 --fields DATE,DESCRIPTION,IN,OUT  # Custom fields
```

### Export Fields

`--fields` accepts a comma-separated list of: `DATE`, `DESCRIPTION`, `INTEREST_DATE`, `IN`, `OUT`, `TO_ACCOUNT`, `FROM_ACCOUNT`, `CATEGORY`, `SUBCATEGORY`.

## Rate Limits

SpareBank 1 allows 60 API calls per hour. On 429 responses the CLI surfaces the `Retry-After` header — wait the indicated time and retry rather than giving up.

## Security Notes

- Credentials and tokens are encrypted on disk (`~/.config/finance/`)
- Tokens are never printed to stdout
- All API calls over HTTPS
