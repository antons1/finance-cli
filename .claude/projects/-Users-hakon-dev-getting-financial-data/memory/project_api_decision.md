---
name: API and app format decisions
description: SpareBank 1 Developer Portal chosen as primary API; CLI app for Claude Code use; Enable Banking as future secondary
type: project
---

SpareBank 1 Developer Portal chosen as primary data source over Enable Banking and other PSD2 aggregators.

**Why:** Most of the user's financial data is in SpareBank 1. The SB1 API offers 60 calls/hour (vs 4/day PSD2 limit), potentially deeper than 90-day transaction history, and securities/investment data — all unavailable through PSD2 aggregators.

**How to apply:** Build against SB1's OAuth2 + BankID flow. Enable Banking can be added later for Bulder Bank and other institutions. The app should be a CLI with machine-friendly output so Claude Code can invoke it as a tool.
