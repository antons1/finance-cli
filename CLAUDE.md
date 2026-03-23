This repository should be used for exploring and building a CLI app for extracting financial data from personal banks.
It is important to prioritize security over all other concerns, as this app will work directly with financial data.

## Decisions
- **Primary API:** SpareBank 1 Developer Portal (`developer.sparebank1.no`) — OAuth2 + BankID, 60 calls/hour, deeper transaction history than PSD2 aggregators.
- **Secondary (future):** Enable Banking for Bulder/other banks if needed.
- **App format:** CLI tool designed to be usable by Claude Code (machine-friendly output).
- Research on Open Banking, aggregators, and bank APIs is in `research/`.
