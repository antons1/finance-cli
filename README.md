# finance

CLI tool for fetching personal financial data from Norwegian bank APIs. Currently supports SpareBank 1.

## Install

```bash
python3 -m pip install -e ".[dev]"
```

## Setup

### 1. Register a client

Go to [developer.sparebank1.no](https://developer.sparebank1.no), log in with BankID, and create a personal client. Set the redirect URL to `http://localhost:11737/callback`.

### 2. Store credentials

```bash
finance auth setup
```

Paste your client ID and secret when prompted. They are encrypted on disk — never stored in plaintext.

### 3. Log in

```bash
finance auth login              # Opens browser for BankID
finance auth login --headless   # Prints URL, you paste the redirect back (for SSH/servers)
```

## Usage

```bash
# Accounts
finance accounts list
finance accounts get ACCOUNT_KEY
finance accounts balance

# Transactions
finance transactions list --account-key KEY
finance transactions list --account-key KEY --from 2026-01-01 --to 2026-03-01
finance transactions details TRANSACTION_ID
finance transactions export --account-key KEY --from 2026-01-01 --to 2026-03-01
finance transactions export --account-key KEY --from 2026-01-01 --to 2026-03-01 --fields DATE,DESCRIPTION,IN,OUT

# Auth
finance auth status
finance auth logout
```

All commands output JSON to stdout (except `export`, which outputs CSV). Errors go to stderr with exit code 1.

### Export fields

`--fields` accepts a comma-separated list: `DATE`, `DESCRIPTION`, `INTEREST_DATE`, `IN`, `OUT`, `TO_ACCOUNT`, `FROM_ACCOUNT`, `CATEGORY`, `SUBCATEGORY`.

## Server deployment (headless/cron)

The CLI can run autonomously on a headless server after initial setup.

### Initial setup (on a machine with a browser)

```bash
finance auth setup
finance auth login
```

### Copy credentials to server

```bash
ssh server "mkdir -p ~/.config/finance"
scp ~/.config/finance/tokens.enc ~/.config/finance/key server:~/.config/finance/
ssh server "chmod 600 ~/.config/finance/tokens.enc ~/.config/finance/key"
```

The refresh token is valid for up to 365 days — no re-authentication needed until it expires.

### Cron example

```cron
0 */6 * * * /path/to/finance accounts balance >> /var/log/finance.log 2>&1
```

## Security

- Credentials and tokens encrypted on disk with Fernet (AES-128-CBC)
- Key and token files are `chmod 600`
- OAuth2 with PKCE and state parameter
- Local callback server binds to `127.0.0.1` only
- All API calls over HTTPS
- Tokens are never printed to stdout

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -v
```

TDD workflow: write tests first, then implement.

## Rate limits

SpareBank 1 allows 60 API calls per hour. The CLI surfaces `Retry-After` on 429 responses.
