# Enable Banking API - Deep Dive Research

Research date: 2026-03-23

## 1. API Structure and Endpoints

Enable Banking provides a **REST API** at `https://api.enablebanking.com`. It is an aggregation
layer that sits between your application and European bank APIs (PSD2/Open Banking APIs). You do
not talk to banks directly -- Enable Banking normalises the interfaces of 4,700+ bank APIs across
29 EEA countries into one unified API.

### Base URL

```
https://api.enablebanking.com
```

(Legacy alias `https://api.tilisy.com` is deprecated.)

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| **GET** | `/aspsps` | List available banks (ASPSPs) with metadata. Filter by country. |
| **GET** | `/application` | Get your application details (name, redirect URLs, etc.) |
| **POST** | `/auth` | Start bank authorization -- returns a redirect URL for the user |
| **POST** | `/sessions` | Exchange authorization code for a session (returns accounts) |
| **GET** | `/sessions/{session_id}` | Get session details |
| **DELETE** | `/sessions/{session_id}` | Delete/revoke a session |
| **GET** | `/accounts/{account_id}/details` | Fetch account details |
| **GET** | `/accounts/{account_id}/balances` | Fetch account balances |
| **GET** | `/accounts/{account_id}/transactions` | Fetch account transactions |
| **GET** | `/accounts/{account_id}/transactions/{transaction_id}` | Fetch single transaction details |
| **POST** | `/payments` | Initiate a payment |
| **GET** | `/payments/{payment_id}` | Get payment status |
| **DELETE** | `/payments/{payment_id}` | Delete finished/failed payment |

### Key Concept: The Flow

1. `GET /aspsps` -- find the bank
2. `POST /auth` -- get redirect URL for user to authenticate at their bank
3. User authenticates at bank, gets redirected back with a `code`
4. `POST /sessions` with the `code` -- creates session, returns `session_id` + list of accounts
5. `GET /accounts/{uid}/balances` and `GET /accounts/{uid}/transactions` -- fetch data

---

## 2. Authentication Flow

### Developer Authentication (JWT)

All API requests require a JWT in the Authorization header. The JWT is signed with your private
key (RSA, RS256 algorithm).

**JWT Header:**
```json
{
  "typ": "JWT",
  "alg": "RS256",
  "kid": "<your_application_id>"
}
```

**JWT Body:**
```json
{
  "iss": "enablebanking.com",
  "aud": "api.enablebanking.com",
  "iat": 1711100000,
  "exp": 1711186400
}
```

- Maximum JWT TTL: **24 hours** (86,400 seconds)
- The private key is a `.pem` file downloaded when you register your application

### Bank Account Linking (End-User Authorization)

This is a redirect-based OAuth-like flow:

1. **Your app** calls `POST /auth` with:
   ```json
   {
     "access": {
       "valid_until": "2026-09-20T00:00:00Z"
     },
     "aspsp": {
       "name": "DNB",
       "country": "NO"
     },
     "state": "random-uuid",
     "redirect_url": "https://yourapp.com/callback",
     "psu_type": "personal"
   }
   ```

2. **API responds** with a URL. You redirect the user to that URL.

3. **User authenticates** at their bank (e.g., BankID in Norway) and grants consent.

4. **Bank redirects** user back to your `redirect_url` with a `code` query parameter.

5. **Your app** calls `POST /sessions` with `{"code": "<the_code>"}`.

6. **API responds** with `session_id` and a list of accessible accounts.

### Norway-Specific Authentication Notes

- **BankID** is the dominant SCA method across Norwegian banks
- **DNB** requires the user's Norwegian national identity number (fodselsnummer) before redirect
- **Nordea** business users must select a brand (Nordea, Nordea Corporate, Nordea First Card)
- **SpareBank 1** users must select their regional entity
- **Danske Bank** supports automatic app-to-app switching to Mobilbank
- **Caveat:** App-to-app switching to Mobile BankID does NOT work when BankID is on the same
  device -- except Danske Bank. Users in WebViews may fail SCA; always open auth URLs in the
  default system browser.

---

## 3. SDK Availability

### Aggregation API (api.enablebanking.com) -- The Main Product

This is a **REST API with no official SDK wrapper**. You use standard HTTP libraries. They provide
code samples in 7 languages:

- **Python** (PyJWT + requests)
- **JavaScript/Node.js**
- **Go**
- **C#**
- **PHP**
- **Ruby**
- **Postman collection**

All samples are at: https://github.com/enablebanking/enablebanking-api-samples

### Direct Connection Library (enablebanking-api on PyPI) -- Separate Product

There is also `pip install enablebanking-api` (v0.5.1) which is a lower-level library for
connecting directly to bank APIs using your own eIDAS/PSD2 certificates. This is a **different
product** (called "aggregation core") intended for licensed TPPs who want to bypass the aggregation
API. It has classes: `MetaApi`, `AuthApi`, `AispApi`, `PispApi`. There are also Java and JS
variants. This is NOT what most developers want.

### CLI Tool

```
pip3 install enablebanking-cli
```

A command-line tool for interacting with the API and control panel. Currently supports `auth`
(login/logout) and `app` management. Future: `accounts`, `payments`, `data-insights`.

GitHub: https://github.com/enablebanking/enablebanking-cli

### Community SDK

- https://github.com/nocfo/enablebanking-python-sdk -- A third-party Python SDK by nocfo
- https://github.com/tech-gian/EnableBanking -- A .NET NuGet package

---

## 4. Data Format (JSON Response Structures)

### Session Response (POST /sessions)

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "accounts": [
    {
      "account_id": { "iban": "NO9386011117947" },
      "all_account_ids": [
        { "identification": "NO9386011117947", "scheme_name": "IBAN" }
      ],
      "account_servicer": {
        "bic_fi": "DNBANOKK",
        "name": "DNB"
      },
      "name": "Brukskonto",
      "currency": "NOK",
      "cash_account_type": "CACC",
      "usage": "PRIV",
      "uid": "abc123-unique-id",
      "identification_hash": "sha256hash..."
    }
  ],
  "aspsp": { "name": "DNB", "country": "NO" },
  "psu_type": "personal",
  "access": { "valid_until": "2026-09-20T00:00:00Z" }
}
```

### Balances Response (GET /accounts/{uid}/balances)

```json
{
  "balances": [
    {
      "name": "Booked Balance",
      "balance_amount": {
        "currency": "NOK",
        "amount": "12345.67"
      },
      "balance_type": "CLBD",
      "reference_date": "2026-03-23",
      "last_change_date_time": "2026-03-23T14:30:00Z"
    }
  ]
}
```

Balance types: `CLBD` (closing booked), `ITAV` (interim available), `XPCD` (expected),
`CLAV`, `FWAV`, `INFO`, `ITBD`, `OPAV`, `OPBD`, `OTHR`, `PRCD`, `VALU`.

### Transactions Response (GET /accounts/{uid}/transactions)

```json
{
  "transactions": [
    {
      "entry_reference": "2026032300001",
      "transaction_amount": {
        "currency": "NOK",
        "amount": "-299.00"
      },
      "credit_debit_indicator": "DBIT",
      "status": "BOOK",
      "booking_date": "2026-03-22",
      "value_date": "2026-03-22",
      "transaction_date": "2026-03-22",
      "creditor": { "name": "REMA 1000" },
      "creditor_account": { "iban": "NO1234567890123" },
      "debtor": { "name": "Ola Nordmann" },
      "debtor_account": { "iban": "NO9386011117947" },
      "remittance_information": ["Varekjop REMA 1000 OSLO"],
      "bank_transaction_code": {
        "description": "Purchase",
        "code": "PMNT",
        "sub_code": "MCOP"
      },
      "balance_after_transaction": {
        "currency": "NOK",
        "amount": "12046.67"
      },
      "merchant_category_code": "5411",
      "reference_number": "1234567890",
      "transaction_id": "temp-id-for-detail-fetch"
    }
  ],
  "continuation_key": "E8GzhnnsFC7K+4e3YMYYKpyM"
}
```

**Pagination:** If `continuation_key` is present, call again with `?continuation_key=<value>` to
get more. Page size varies per bank. You may receive **empty transactions with a continuation_key**
-- keep fetching until no key is returned.

Query parameters: `date_from`, `date_to`, `continuation_key`.

---

## 5. Session Management

### Session Lifetime

- You set session validity via `access.valid_until` in the `POST /auth` request
- Maximum consent validity is bank-dependent, returned in `maximum_consent_validity` per ASPSP
  (value in seconds). For most banks: **180 days** (~6 months)
- Enable Banking handles access token refresh internally -- you do not manage bank tokens

### Re-Authorization

- There is NO token refresh mechanism for sessions. When a session expires, you must start a
  new authorization flow (redirect user to bank again)
- Recommended: notify users before session expiration and prompt re-authorization

### Premature Expiration

Sessions can expire before `valid_until` for reasons including:
- Bank-side revocation
- Single-session restrictions (new consent invalidates old one)
- KYC requirements
- Certificate migrations
- Sandbox limitations

You will receive an `EXPIRED_SESSION` error. Handle it by initiating a new auth flow.

### Rate Limits

- Background fetches (no PSU headers): typically limited to **4 requests per day** per account
  by the banks themselves
- Online fetches (with PSU headers): no strict limit, but user must be actively present
- 429 errors: retry after 6+ hours; no bypass

### PSU Headers Rule

- If user is actively browsing: include `Psu-Ip-Address` and `Psu-User-Agent` headers
- If background/batch fetch: include **NO** PSU headers at all
- Mixing (some headers but not all) causes `422 PSU_HEADER_NOT_PROVIDED` errors

---

## 6. Developer Experience

### Sign-Up to First API Call

1. Go to https://enablebanking.com/sign-in/
2. Enter email -- account is auto-created on first sign-in (magic link, no password)
3. Access Control Panel
4. Register an application (sandbox environment selected by default)
5. Enter app name and whitelist redirect URLs
6. Download the private key `.pem` file (contains your application ID)
7. Write code to generate JWT, call `POST /auth`, handle redirect, call `POST /sessions`

**Time estimate:** You can make your first sandbox API call within 30 minutes if you follow the
quick start guide.

### What's Good

- Very clean REST API with few endpoints to learn
- JWT auth is straightforward (no OAuth client credentials dance for the developer side)
- Unified data format across all banks
- Good Python example code that covers the full flow
- Control panel for monitoring, logs, and configuration

### What's Rough

- No official SDK -- you write raw HTTP calls
- Private key management (`.pem` file download during registration, must store securely)
- Redirect flow means you need a web server or at least a callback URL handler
- Production requires a signed contract + KYB process
- Volume-based pricing is opaque (must contact sales)

---

## 7. Sandbox

### Mock ASPSP

Enable Banking provides a "Mock ASPSP" -- a simulated bank controlled via the control panel.
This is your primary testing tool.

- Controllable via the Enable Banking control panel UI
- Synthetic data samples available for download
- Transactions returned in batches of 10, most recent first
- **No payment initiation** in Mock ASPSP

### Real Bank Sandboxes

Some real bank sandboxes are available, but Enable Banking explicitly warns that bank sandboxes
often do not accurately simulate production behavior. Available sandbox credentials include:

**Norwegian banks in sandbox:**
- **Nordea** (NO): No credentials needed
- **Handelsbanken**: Supports date-based filtering

**Other notable sandboxes:**
- DKB (DE): aspsp1/aspsp1
- BBVA (ES/IT/PT/FR/BE): user1/1234
- Various others with OTP codes typically "123456"

### Sandbox Limitations

- Bank sandboxes may be unstable independently of production
- Not all filtering features work in all sandboxes
- Single-tenant (TPP IaaS) users only get Mock ASPSP by default
- Shared infrastructure recommended for broader sandbox testing

---

## 8. Documentation Quality

### Location

- Main docs: https://enablebanking.com/docs
- API reference: https://enablebanking.com/docs/api/reference/
- Quick start: https://enablebanking.com/docs/api/quick-start/
- Sandbox: https://enablebanking.com/docs/api/sandbox/
- FAQ: https://enablebanking.com/docs/faq/
- Market specifics: https://enablebanking.com/docs/markets/ (per-country details)
- Norway specifics: https://enablebanking.com/docs/markets/no/

### Assessment

**Strengths:**
- API reference is thorough with full request/response schemas
- FAQ is excellent -- covers real-world gotchas (PSU headers, rate limits, premature expiry)
- Country-specific docs are valuable (Norway page covers BankID, DNB ID requirements, etc.)
- Quick start guide is clear and step-by-step

**Weaknesses:**
- No interactive API explorer (Swagger UI)
- JSON examples in the API reference could be more complete
- The docs site requires JavaScript (won't render without it)
- Some pages are thin on detail (market pages vary in depth)

---

## 9. Code Examples

### Official GitHub Repositories

| Repository | Description |
|-----------|-------------|
| [enablebanking-api-samples](https://github.com/enablebanking/enablebanking-api-samples) | Samples in Python, JS, Go, C#, PHP, Ruby, Postman |
| [enablebanking-cli](https://github.com/enablebanking/enablebanking-cli) | CLI tool (Python) |
| [OpenBankingPythonExamples](https://github.com/enablebanking/OpenBankingPythonExamples) | Python examples for the core library (direct bank connections) |
| [OpenBankingJSExamples](https://github.com/enablebanking/OpenBankingJSExamples) | JS examples for the core library |
| [OpenBankingJavaExamples](https://github.com/enablebanking/OpenBankingJavaExamples) | Java examples for the core library |
| [open_banking_eidas_broker](https://github.com/enablebanking/open_banking_eidas_broker) | eIDAS certificate broker microservice |

### Key Python Example (Account Information)

The reference Python example at `enablebanking-api-samples/python_example/account_information.py`
demonstrates the complete flow:

1. Load config (applicationId, keyPath)
2. Generate JWT with PyJWT
3. GET /application to verify setup
4. GET /aspsps to list banks
5. POST /auth to start authorization (hardcoded to Nordea FI in the example)
6. Print auth URL for user to visit
7. Read redirected URL from stdin, extract `code`
8. POST /sessions to create session
9. GET /accounts/{uid}/balances
10. GET /accounts/{uid}/transactions with continuation_key loop

Dependencies: `requests`, `pyjwt`

### Community Projects

- [nocfo/enablebanking-python-sdk](https://github.com/nocfo/enablebanking-python-sdk) -- Python SDK wrapper
- [tech-gian/EnableBanking](https://github.com/tech-gian/EnableBanking) -- .NET NuGet package

---

## 10. Limitations and Quirks

### Data NOT Available

- **Historical balances on specific past dates** -- you cannot ask "what was my balance on Jan 1?"
- **Individual transactions within clearing batches** -- banks only expose aggregated settlements
- **Bundled transaction breakdowns** -- if a bank bundles clearing, you see one line
- **Currency "XXX"** -- some accounts return unknown currency code; your app must handle this

### Transaction History Limits

- Most banks provide **at least 1 year** of history; some offer 2-3+ years
- However, many banks restrict the initial fetch to **90 days** from authorization
  (there is roughly a 1-hour window after first authorization for longer history)
- Use `strategy=longest` parameter to attempt maximum available history

### Identifier Quirks

- **No stable ASPSP IDs** -- banks are identified by `(name, country)` tuple. Banks rebrand.
  Always fetch fresh ASPSP lists.
- **BICs are not unique** -- cannot use as identifiers (banks operate multiple brands per BIC)
- **`entry_reference`** is the reliable transaction identifier across sessions (but not globally
  unique, only unique per account)
- **`transaction_id`** is TEMPORARY -- only valid for fetching details within a session, never
  use for cross-session matching

### UI Constraints

- **Cannot use iframes** for bank auth -- CORS restrictions prevent it
- **WebViews break BankID** -- always use default system browser for auth URLs

### Rate Limits

- Background fetches: ~4 per day per account (bank-imposed)
- No way to bypass bank rate limits

### Production Access

- Requires signed contract + KYB
- Volume-based pricing (must contact sales@enablebanking.com)
- Free sandbox access available before contract

### Norwegian-Specific Quirks

- DNB requires national identity number pre-authentication
- SpareBank 1 users must select their specific regional bank entity
- Mobile BankID app-to-app switching generally does not work (except Danske Bank)
- NOK domestic payments supported; SEPA in EUR supported; instant NOK via Straks supported
- SCT Instant (EUR) not supported by most Norwegian banks
- Payee name verification is NOT required for NOK payments (Financial Contracts Act)

---

## Summary Assessment for Personal Bank Data Access (Norway)

**Viability:** Enable Banking is a strong option for accessing Norwegian bank data. It covers the
major banks (DNB, Nordea, SpareBank 1, Handelsbanken, Danske Bank) with BankID authentication.

**Key trade-offs:**
- (+) Single API for all Norwegian banks
- (+) Handles token refresh and bank API differences internally
- (+) Clean REST API, easy to understand
- (+) Free sandbox for experimentation
- (-) No free production tier -- requires contract and volume-based pricing
- (-) No official SDK, just HTTP examples
- (-) 180-day max session means periodic re-authorization
- (-) Background fetch rate limits (4/day) may be restrictive for real-time use cases
- (-) Initial transaction history may be limited to 90 days by some banks

**Alternative to consider:** GoCardless (formerly Nordigen) offers a free tier for personal use
and covers Norwegian banks. Worth comparing directly.
