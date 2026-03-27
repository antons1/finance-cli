This repository should be used for exploring and building a CLI app for extracting financial data from personal banks.
It is important to prioritize security over all other concerns, as this app will work directly with financial data.

## Decisions
- **Primary API:** SpareBank 1 Developer Portal (`developer.sparebank1.no`) — OAuth2 + BankID, 60 calls/hour, deeper transaction history than PSD2 aggregators.
- **Secondary (future):** Enable Banking for Bulder/other banks if needed.
- **App format:** CLI tool designed to be usable by Claude Code (machine-friendly output).
- Research on Open Banking, aggregators, and bank APIs is in `research/`.

## CLI Usage

Install: `python3 -m pip install -e ".[dev]"`

### Setup & Auth
```bash
finance auth setup          # Enter client_id and client_secret (stored encrypted)
finance auth login           # Interactive BankID login (opens browser)
finance auth login --headless  # Headless: prints URL, you paste redirect back
finance auth status          # Check auth status (JSON)
finance auth logout          # Clear all tokens
```

### Accounts & Transactions
```bash
finance --json accounts list                              # List all accounts (JSON)
finance --json accounts get ACCOUNT_KEY                   # Get single account
finance --json accounts balance                           # Balance summary
finance --json transactions list --account-key KEY        # List transactions
finance --json transactions list --account-key KEY --from 2026-01-01 --to 2026-03-01
finance --json transactions details TRANSACTION_ID        # Transaction details
finance transactions export --account-key KEY --from 2026-01-01 --to 2026-03-01  # Export (CSV)
```

Note: `--json` is required for all data commands. Export always outputs CSV.

## Security
- Tokens and credentials are encrypted on disk (`~/.config/finance/tokens.enc`) using Fernet (AES-128-CBC)
- Encryption key is in `~/.config/finance/key` (chmod 600)
- Never commit `.env`, `*.pem`, `tokens.enc`, or `key` files
- All API calls use HTTPS only
- OAuth2 with PKCE and state parameter for CSRF protection

## Development
- **TDD**: Write tests first, then implement
- Run tests: `python3 -m pytest tests/ -v`
- Project structure: `src/finance/` with providers under `providers/sb1/`
