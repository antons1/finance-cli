# SpareBank 1 Developer Portal API -- Deep Dive

**Research date: 2026-03-26**

**Source:** https://developer.sparebank1.no, GitHub tutorials, API catalog endpoint, community projects.

---

## Executive Summary

The SpareBank 1 Developer Portal offers a rich proprietary API that goes significantly beyond what PSD2 aggregators provide. It includes **personal banking accounts, transactions, transfers, credit cards, credit accounts, securities/investments, document archives, and user identity**. Authentication uses OAuth 2.0 with BankID. The API is available to personal customers of any SpareBank 1 bank (12 banks in the alliance).

**Key advantage over PSD2 aggregators:** Deeper data (securities, credit card details, document archive, classified transactions), write access (transfers), and longer token lifetime (refresh tokens valid up to 365 days).

**Key limitation:** Only works for SpareBank 1 banks. Other banks (Bulder, Nordnet) require a separate solution.

---

## Table of Contents

1. [Authentication & OAuth 2.0](#1-authentication--oauth-20)
2. [API Base URLs & Headers](#2-api-base-urls--headers)
3. [Rate Limits](#3-rate-limits)
4. [Financial Institutions (Banks)](#4-financial-institutions-banks)
5. [Personal Banking Accounts API](#5-personal-banking-accounts-api)
6. [Transactions API](#6-transactions-api)
7. [Transfer API](#7-transfer-api)
8. [Credit Account API](#8-credit-account-api)
9. [Credit Card API](#9-credit-card-api)
10. [Securities (Verdipapirer) API](#10-securities-verdipapirer-api)
11. [Document Archive API](#11-document-archive-api)
12. [User Identity API](#12-user-identity-api)
13. [Account Owner Verification API](#13-account-owner-verification-api)
14. [Corporate (Business) APIs](#14-corporate-business-apis)
15. [Hello World / Testing API](#15-hello-world--testing-api)
16. [Personal Client vs Partner Client](#16-personal-client-vs-partner-client)
17. [Data Models (Known Fields)](#17-data-models-known-fields)

---

## 1. Authentication & OAuth 2.0

### Flow: OAuth 2.0 Authorization Code with PKCE

The API uses **OAuth 2.0 Authorization Code Flow** (RFC 6749 Section 4.1) with **PKCE** (RFC 7636) and **BankID** as the identity provider.

### Endpoints

| Purpose | URL |
|---------|-----|
| Authorization | `https://api.sparebank1.no/oauth/authorize` |
| Token Exchange | `https://api.sparebank1.no/oauth/token` |
| Logout | `https://api.sparebank1.no/oauth/logout` |

### Authorization Request Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | Application identifier from registration |
| `redirect_uri` | Yes | Must match pre-configured URI |
| `response_type` | Yes | Always `code` |
| `code_challenge` | Yes | Base64-URL-encoded SHA-256 hash of `code_verifier` (PKCE) |
| `code_challenge_method` | Yes | Must be `S256` |
| `finInst` | No | Bank identifier (e.g., `fid-smn`). If omitted, user sees bank picker. |
| `state` | No | CSRF protection (UUID recommended) |
| `scope` | No | Space-separated. Must include `openid` if used. Also supports `pid`, `email`, `phone`. |
| `market` | No | `B` for business, `p` for private (default: private) |
| `nonce` | No | Replay attack prevention (UUID) |
| `loginMethod` | No | Pre-set login method, e.g. `bankid_oidc` |

### Token Exchange (POST)

```bash
curl --location --request POST 'https://api.sparebank1.no/oauth/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --header 'Authorization: Basic <Base64(client_id:client_secret)>' \
  --data-urlencode 'code=AUTHENTICATION_CODE' \
  --data-urlencode 'grant_type=authorization_code' \
  --data-urlencode 'code_verifier=CODE_VERIFIER' \
  --data-urlencode 'redirect_uri=REDIRECT_URI'
```

### Token Response

```json
{
    "access_token": "ACCESS_TOKEN",
    "token_type": "Bearer",
    "expires_in": 300,
    "refresh_token_expires_in": 2591999,
    "refresh_token_absolute_expires_in": 31535999,
    "refresh_token": "REFRESH_TOKEN",
    "scope": "openid",
    "id_token": "ID_TOKEN"
}
```

### Token Lifetimes

| Token | Lifetime | Notes |
|-------|----------|-------|
| Authorization code | 2 minutes | Single use only |
| Access token | **5 minutes** (default, configurable) | JWT Bearer token |
| Refresh token (idle) | **~30 days** (default, configurable up to 60 days) | Invalid if not used within this period |
| Refresh token (absolute) | **~365 days** (default, configurable up to 1 year) | Maximum lifetime regardless of refresh activity |

**Note:** Older documentation says 10 minutes for access tokens; the latest partner OAuth docs say 5 minutes (configurable). Personal client tokens may differ.

### Refresh Token Flow

```bash
curl --location --request POST 'https://api.sparebank1.no/oauth/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --header 'Authorization: Basic <Base64(client_id:client_secret)>' \
  --data-urlencode 'refresh_token=REFRESH_TOKEN' \
  --data-urlencode 'grant_type=refresh_token'
```

### ID Token Claims (when scope includes `openid`)

| Field | Description |
|-------|-------------|
| `sub` | SHA-256 hash of national identity number |
| `name` | "surname, firstname" |
| `email` | Email (if `scope=email`) |
| `phone_number` | Phone (if `scope=phone`) |
| `pid` | Norwegian national identity number (if `scope=pid`) |
| `financial_institution_id` | e.g., `fid-sr-bank` |
| `sb1-auth-strength` | 0-10, max 10 for BankID |
| `aud` | client_id |
| `iss` | Identity provider URL |
| `exp` / `iat` | Expiry / issued-at timestamps |
| `nonce` | Echo of request nonce |

---

## 2. API Base URLs & Headers

**Base URL:** `https://api.sparebank1.no`

### Required Headers

| Header | Value | Notes |
|--------|-------|-------|
| `Authorization` | `Bearer {access_token}` | Required for all authenticated endpoints |
| `Accept` | `application/vnd.sparebank1.v5+json; charset=utf-8` | Version varies by API. v5 for accounts, v1 for most others. |
| `Content-Type` | `application/vnd.sparebank1.v1+json; charset=utf-8` | Required for POST/PUT requests |

---

## 3. Rate Limits

| Limit | Value | Source |
|-------|-------|--------|
| API calls per hour | **60** | Confirmed by pengerobot integration docs |
| Rate limit response | HTTP 429 | With `Retry-After` header |

**Practical impact:** With 60 calls/hour, monitoring 4 accounts (balance check per account) plus transaction fetches uses capacity quickly. Plan API calls carefully.

---

## 4. Financial Institutions (Banks)

**No authentication required.**

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/common/financial-institutions/all` | All financial institutions (banks + non-banks) |
| GET | `/common/financial-institutions/banks` | Only banks in the SpareBank 1 alliance |
| GET | `/common/financial-institutions/domainDisplayNames` | Display names for domains |

### Available Banks (12)

| ID | Name |
|----|------|
| `fid-gudbrandsdal` | SpareBank 1 Gudbrandsdal |
| `fid-hallingdal-valdres` | SpareBank 1 Hallingdal Valdres |
| `fid-helgeland` | SpareBank 1 Helgeland |
| `fid-lom-skjaak` | SpareBank 1 Lom og Skjaak |
| `fid-nord-norge` | SpareBank 1 Nord-Norge |
| `fid-nordmore` | SpareBank 1 Nordmore |
| `fid-ringerike-hadeland` | SpareBank 1 Ringerike Hadeland |
| `fid-smn` | SpareBank 1 SMN |
| `fid-sogn-fjordane` | SpareBank 1 Sogn og Fjordane |
| `fid-sor-norge` | SpareBank 1 Sor-Norge |
| `fid-ostfold-akershus` | SpareBank 1 Ostfold Akershus |
| `fid-ostlandet` | SpareBank 1 Ostlandet |

### Response Fields

```json
{
  "financialInstitutions": [
    {
      "id": "fid-smn",
      "shortName": "smn",
      "name": "SpareBank 1 SMN",
      "bankplassregisterNumber": "...",
      "authorizeUrl": "https://api.sparebank1.no/oauth/authorize?finInst=fid-smn",
      "type": "bank"
    }
  ]
}
```

---

## 5. Personal Banking Accounts API

**Base path:** `/personal/banking/accounts`
**Accept header version:** `application/vnd.sparebank1.v5+json`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/accounts` | List all banking accounts |
| GET | `/personal/banking/accounts/{accountKey}` | Get specific account by key |
| GET | `/personal/banking/accounts/default` | Get default payment account |
| GET | `/personal/banking/accounts/{accountKey}/details` | Get account details |
| GET | `/personal/banking/accounts/{accountKey}/roles` | Get account roles/permissions |
| GET | `/personal/banking/accounts/keys` | Get account keys |
| POST | `/personal/banking/accounts/balance` | Get balance for specific account(s) |
| GET | `/personal/banking/accounts/child/{id}` | Get child account info |

### Query Parameters (GET /accounts)

From the pengerobot integration, the accounts endpoint supports these filter parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `includeNokAccounts` | boolean | true | Include NOK-denominated accounts |
| `includeCurrencyAccounts` | boolean | true | Include foreign currency accounts |
| `includeBsuAccounts` | boolean | true | Include BSU (tax-favored savings) accounts |
| `includeCreditCardAccounts` | boolean | true | Include credit card accounts |
| `includeAskAccounts` | boolean | false | Include ASK (equity savings) accounts |
| `includePensionAccounts` | boolean | false | Include pension accounts |

### Account Data Model (from Swagger v1.4, likely similar in v5)

```json
{
  "id": "string (account key for API calls)",
  "accountNumber": {
    "value": "12345678901",
    "formatted": "1234 56 78901"
  },
  "name": "Account system name",
  "description": "User description",
  "balance": {
    "amount": 12345.67,
    "currencyCode": "NOK"
  },
  "availableBalance": {
    "amount": 12345.67,
    "currencyCode": "NOK"
  },
  "owner": {
    "name": "Ola Nordmann",
    "firstName": "Ola",
    "lastName": "Nordmann"
  },
  "product": "string (account product code)",
  "type": "string (account type)",
  "interestRate": 3.5,
  "freeWithdrawalsLeft": 10,
  "_links": {}
}
```

### Balance Request (POST)

```json
POST /personal/banking/accounts/balance
Content-Type: application/vnd.sparebank1.v1+json; charset=utf-8

{"accountNumber": "12345678901"}
```

---

## 6. Transactions API

**Base path:** `/personal/banking/transactions`
**Accept header version:** `application/vnd.sparebank1.v1+json`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/transactions` | Get transactions (requires `accountKey` query param) |
| GET | `/personal/banking/transactions/{id}/details` | Get transaction details |
| GET | `/personal/banking/transactions/{id}/details/classified` | Get classified transaction details (with category) |
| GET | `/personal/banking/transactions/classified` | Get all transactions with classification |
| GET | `/personal/banking/transactions/export` | Export transactions (likely CSV) |

### Query Parameters

| Parameter | Description |
|-----------|-------------|
| `accountKey` | Required. The account key from the Accounts API |

### Transaction Data Model (from Swagger v1.4)

```json
{
  "amount": {
    "amount": -150.00,
    "currencyCode": "NOK"
  },
  "accountingDate": "2026-03-25",
  "description": "REMA 1000 MIDTBYEN",
  "fullDescription": "Original unparsed transaction text",
  "archiveReference": "string",
  "remoteAccount": "98765432101",
  "transactionCode": "string (type code)",
  "transactionType": "Human-readable type description",
  "_links": {}
}
```

**Classified transactions** additionally include spending category information (the "classified" endpoints).

### Export

The `/personal/banking/transactions/export` endpoint can export transactions, likely in CSV format (confirmed by the Go client which exports with fields: Date, Payee, Category, Memo, Outflow, Inflow).

---

## 7. Transfer API

**Base path:** `/personal/banking/transfer`
**Accept header version:** `application/vnd.sparebank1.v1+json`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/personal/banking/transfer/debit` | Transfer between own accounts |
| POST | `/personal/banking/transfer/creditcard/transferTo` | Transfer to credit card |
| POST | `/personal/banking/transfer/pension` | Transfer to/from pension account |

### Debit Transfer Request

```json
POST /personal/banking/transfer/debit
Content-Type: application/vnd.sparebank1.v1+json

{
  "fromAccount": "18133339244",
  "toAccount": "18135319992",
  "amount": "100.00",
  "currencyCode": "NOK",
  "message": "Description text",
  "dueDate": "2026-03-27"
}
```

### Credit Card Transfer Request

```json
POST /personal/banking/transfer/creditcard/transferTo

{
  "fromAccount": "12345678901",
  "creditCardAccountId": "...",
  "amount": "500.00",
  "dueDate": "2026-03-27"
}
```

### Supported Currencies

NOK, EUR, USD, SEK, DKK, GBP

### Constraints

- Transfers are limited to the user's own accounts only
- Amount range: 0.01 to 999999999
- Non-NOK transfers may incur additional costs

---

## 8. Credit Account API

**Base path:** `/personal/banking/credit/accounts`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/credit/accounts` | List all credit accounts |
| GET | `/personal/banking/credit/accounts/{accountId}` | Get specific credit account |
| GET | `/personal/banking/credit/accounts/{accountId}/payment-info` | Payment information |
| GET | `/personal/banking/credit/accounts/{accountId}/dueday` | Get due day |
| POST | `/personal/banking/credit/accounts/{accountId}/dueday` | Update due day |
| GET | `/personal/banking/credit/accounts/{accountId}/fees` | Get fee information (v4) |
| GET | `/personal/banking/credit/accounts/{accountId}/transactions` | Credit account transactions |
| GET | `/personal/banking/credit/accounts/{accountId}/transactions/{transactionId}` | Specific transaction |
| GET | `/personal/banking/credit/accounts/{accountId}/transactions/authorizations` | Pending authorizations |
| GET | `/personal/banking/credit/accounts/{accountId}/transactions/statements` | Account statements |
| GET | `/personal/banking/credit/accounts/{accountId}/transactions/export/transactions.csv` | Export as CSV |
| GET | `/personal/banking/credit/accounts/digitalbank-oversikt` | Overview for digital banking |

---

## 9. Credit Card API

**Base path:** `/personal/banking/credit/cards`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/credit/cards` | List all credit cards |
| GET | `/personal/banking/credit/cards/{cardId}` | Get specific card |
| PUT | `/personal/banking/credit/cards/{cardId}/status` | Update card status (block/unblock) |
| GET | `/personal/banking/credit/cards/{cardId}/regionalblocking` | Get regional blocking settings |
| PUT | `/personal/banking/credit/cards/{cardId}/regionalblocking` | Update regional blocking |
| GET | `/personal/banking/credit/cards/{cardId}/authorizations` | List pending authorizations |
| GET | `/personal/banking/credit/cards/{cardId}/authorizations/{authorizationId}` | Get specific authorization |

---

## 10. Securities (Verdipapirer) API

**Base path:** `/personal/banking/securities`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/securities` | List all securities/portfolios |
| GET | `/personal/banking/securities/including-disposed` | Include disposed securities |
| GET | `/personal/banking/securities/oversikt` | Securities overview |
| GET | `/personal/banking/securities/customerinfo` | Customer securities info |
| GET | `/personal/banking/securities/stocks/access` | Check stock trading access |
| GET | `/personal/banking/securities/stocks/saml` | SAML for stock trading service |
| POST | `/personal/banking/securities/stocks/saml` | Submit SAML for stock trading |
| GET | `/personal/banking/securities/stocks/saml/share-savings-account/{portfolioId}` | SAML for ASK (share savings) |
| POST | `/personal/banking/securities/stocks/stocktradingservice` | Stock trading service access |
| POST | `/personal/banking/securities/stocks/stocktradingservice/share-savings-account` | ASK trading service |
| PATCH | `/personal/banking/securities/stocks/stocktradingservice/share-savings-account/vps-account-number` | Update VPS account number |
| GET | `/personal/banking/securities/vps-investor-jump-data` | VPS investor data |
| GET | `/personal/banking/securities/widget/savings` | Savings widget data |
| GET | `/personal/banking/securities/widget/savings/ask` | ASK savings widget |
| GET | `/personal/banking/securities/portfolio-performance/ask/{portfolioId}` | ASK portfolio performance |
| GET | `/personal/banking/securities/portfolio-performance/fri` | Free portfolio performance |
| GET | `/personal/banking/securities/kyc/notification` | KYC notification status |
| GET | `/personal/banking/securities/kyc/questions` | KYC questions |
| POST | `/personal/banking/securities/kyc/notification` | Submit KYC notification |
| POST | `/personal/banking/securities/kyc/answers` | Submit KYC answers |

---

## 11. Document Archive API

**Base path:** `/personal/banking/document-archive`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/personal/banking/document-archive` | List all documents |
| GET | `/personal/banking/document-archive/{documentId}` | Get specific document |
| GET | `/personal/banking/document-archive/types` | List document types |
| GET | `/personal/banking/document-archive/messages` | List messages |
| GET | `/personal/banking/document-archive/messages/{messageId}` | Get specific message |
| GET | `/personal/banking/document-archive/zipped` | Download documents as ZIP |
| GET | `/personal/banking/document-archive/signed-documents/{documentId}/details` | Signed document details |
| GET | `/personal/banking/document-archive/signed-documents/{documentId}/pdf` | Download signed document PDF |
| GET | `/personal/banking/document-archive/signed-documents/{documentId}/sdo` | Get SDO (signed data object) |
| GET | `/personal/banking/document-archive/signed-documents/{documentId}/sdo/{index}/pdf` | Get SDO as PDF |

---

## 12. User Identity API

**Base path:** `/common/user`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/common/user/identity/personalid` | Get unique persistent customer identifier |
| GET | `/common/user/info` | Get user info (name, email, phone, DOB) |

### Response: `/common/user/info`

```json
{
  "customerNumber": "12345678901",
  "firstName": "Ola",
  "lastName": "Nordmann",
  "dateOfbirth": "1999-12-31",
  "sub": "cf33c1add8025a",
  "mobilePhoneNumber": "99999999",
  "email": "post@sb1.no"
}
```

### Response: `/common/user/identity/personalid`

```json
{
  "pid": "1234-5678-9-12345"
}
```

---

## 13. Account Owner Verification API

**Base path:** `/common/account-owner/verify`

Verifies whether a Norwegian account belongs to a given person or organization. Uses the KAR (Konto- og Adresseringsregisteret) service provided by Bits AS.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/common/account-owner/verify/personal` | Verify personal account ownership (requires account number + national ID) |
| POST | `/common/account-owner/verify/organization` | Verify organization account ownership (requires account number + org number) |

**Note:** This API only confirms or denies ownership. It cannot be used to look up the owner of an account or list accounts owned by a person.

---

## 14. Corporate (Business) APIs

These APIs require a **partner client** (not personal client) and are for business/corporate banking.

### Corporate Accounts (`/corporate/banking/accounts`)
- Account groups management (CRUD)
- Account listing and balance
- Historical balance
- Documents
- Withdrawals and approvals

### Corporate Authorization (`/corporate/banking/authorization`)
- Agreement management
- Session management (logout, keepalive)

### Corporate Customer Info (`/corporate/banking/customer`)
- Contact information
- Consents, roles, terms and conditions

### Corporate Debit Cards (`/corporate/banking/debitcards`)
- Card listing, ordering, blocking
- Transaction history
- PIN management
- Regional blocking

### Corporate Organizations (`/corporate/banking/organisations`)
- List organizations connected to user
- Business interests

### Kredittbanken Partner (`/credit/partner`)
- Credit card account and transaction data for partners
- Card blocking
- Wallet provisioning (Apple Pay, Google Pay, Click to Pay)
- Customer information

---

## 15. Hello World / Testing API

**No rate limit impact confirmed.**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/common/helloworld` | Simple test endpoint |
| GET | `/common/helloworld/ping` | Ping |
| GET | `/common/helloworld/pong` | Pong |

---

## 16. Personal Client vs Partner Client

| Aspect | Personal Client | Partner Client |
|--------|----------------|----------------|
| **Target** | Individual customers accessing own data | Businesses/partners accessing customer data |
| **Registration** | Self-service on developer portal with BankID | Assigned by the bank |
| **APIs accessible** | Personal banking (pm-*) + common APIs | Corporate (bm-*) + partner APIs + common |
| **OAuth flow** | Authorization Code with PKCE | Authorization Code with PKCE (or Federated/Certificate) |
| **Use case** | Personal finance tools, CLI apps | Commercial products, integrations |

### Partner Authentication Options
1. **OAuth Authorization Code Flow** (OIDC + BankID)
2. **Federated Authentication Flow** (SAML-based)
3. **Certificate Authentication Flow** (mTLS)

---

## 17. Data Models (Known Fields)

### Error Response

```json
{
  "errors": [
    {
      "code": "string",
      "message": "string",
      "traceId": "string"
    }
  ]
}
```

### HATEOAS Links

All responses include `_links` objects for resource navigation (HAL-style).

---

## Key Takeaways for Our CLI App

1. **Registration:** Log into https://developer.sparebank1.no with BankID, create a "personal client" (personlig klient). Get `client_id`, `client_secret`, and `redirect_uri`.

2. **Auth flow for CLI:** The OAuth flow requires a browser for BankID login. The CLI should:
   - Start a local HTTP server on the redirect_uri port
   - Open the browser to the authorization URL
   - Catch the callback with the authorization code
   - Exchange for tokens
   - Store tokens securely (refresh token valid up to 365 days)

3. **Key endpoints for financial data extraction:**
   - `GET /personal/banking/accounts` -- list all accounts
   - `GET /personal/banking/transactions?accountKey=...` -- get transactions
   - `GET /personal/banking/transactions/classified` -- transactions with spending categories
   - `GET /personal/banking/transactions/export` -- CSV export
   - `GET /personal/banking/credit/accounts/{id}/transactions` -- credit card transactions
   - `GET /personal/banking/securities` -- investment portfolio data
   - `POST /personal/banking/accounts/balance` -- real-time balance check

4. **Rate limit strategy:** 60 calls/hour means we need to batch requests efficiently. A single "sync all data" operation might use:
   - 1 call for accounts list
   - N calls for transaction pages (one per account)
   - Optionally 1 call for securities
   - Total: ~N+2 calls per sync

5. **Token management:** Refresh tokens last up to 365 days, so the CLI can maintain long-lived sessions without requiring BankID re-authentication more than once per year.

---

## Sources

- [SpareBank 1 Developer Portal](https://developer.sparebank1.no/)
- [sb1-personal-client-python-tutorial](https://github.com/SpareBank1/sb1-personal-client-python-tutorial)
- [sb1-open-api-tutorial](https://github.com/SpareBank1/sb1-open-api-tutorial)
- [sparebank1-personligklient (Go client with Swagger spec)](https://github.com/johnksv/sparebank1-personligklient)
- [sparebank1_pengerobot (Home Assistant integration)](https://github.com/remimikalsen/sparebank1_pengerobot)
- [Fintech for Dummies workshop](https://sparebank1.github.io/sb1fs/)
- [SpareBank 1 Open APIs (corporate page)](https://www.sparebank1.no/nb/bank/bedrift/open-api.html)
- [SpareBank 1 SMN PSD2 Portal](https://psd2.smn.no/developer/)
- API catalog fetched from `https://developer.sparebank1.no/api/applicationcatalog/apis` (2026-03-26)
- Partner OAuth docs fetched from `https://developer.sparebank1.no/api/documentation/partnerOAuthFlow` (2026-03-26)
