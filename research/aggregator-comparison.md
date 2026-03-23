# Open Banking Aggregator API Comparison for Norwegian Banks

**Research date: 2026-03-23**

**Goal:** Access personal bank data (accounts, balances, transactions) from Norwegian banks, specifically Bulder (Sparebanken Norge), SpareBank 1, and ideally Nordnet. Preference for free options. No business entity.

---

## Summary / Recommendation

**Best option: Enable Banking** -- free for personal/individual non-commercial use via "restricted application" mode. Covers Norway including Sparebanken Norge and SpareBank 1. Finnish company, registered AISP with FIN-FSA. No business entity required for personal use.

**Runner-up: GoCardless Bank Account Data** -- was the gold standard for free open banking, but **new signups are disabled as of July 2025**. Only available if you already have an account.

**Also worth considering: Tink** -- has confirmed coverage of Bulder Bank, SpareBank 1, and Nordnet. Self-service signup at console.tink.com. But pricing starts at ~EUR 0.50/user/month (no free production tier).

---

## 1. GoCardless Bank Account Data (formerly Nordigen)

| Aspect | Details |
|--------|---------|
| **Status** | **NEW SIGNUPS DISABLED as of July 2025.** Existing accounts continue to work. No timeline given for resumption. |
| **Pricing (was)** | Free tier: up to 50 bank connections/month. Paid tiers existed for higher volume. |
| **Rate limits (was)** | Max 4 API calls/day per account (bank-imposed). Each endpoint (details, balances, transactions) counted separately. |
| **Norwegian banks** | Covered Norwegian banks under PSD2/EEA. Specific bank list no longer easily accessible. |
| **Business entity** | Was not required for free tier -- individual developers could sign up. |
| **TPP status** | GoCardless acted as the licensed TPP on your behalf. |
| **API quality** | Well-documented REST API. Good developer experience. Widely used by personal finance tools (Actual Budget, Firefly III). |
| **Verdict** | **Dead end for new users.** If you already have an account, it remains the best free option. |

Sources:
- [GoCardless Developer Docs](https://developer.gocardless.com/bank-account-data/overview)
- [GoCardless New Signups Disabled](https://bankaccountdata.gocardless.com/new-signups-disabled)
- [Actual Budget GoCardless Setup](https://actualbudget.org/docs/advanced/bank-sync/gocardless/)

---

## 2. Enable Banking (Finnish)

| Aspect | Details |
|--------|---------|
| **Pricing** | Volume-based for commercial use (contact sales). **Free for individual non-commercial use** via "restricted application" mode. |
| **Free tier details** | Create a production app, activate in "restricted mode" by linking your own bank accounts. You can only fetch data from accounts you personally link. No contract needed. |
| **Norwegian banks** | **Norway is a supported country (31 countries total).** Documented major banks: DNB, SpareBank 1, Nordea, Handelsbanken, Danske Bank, **Sparebanken Norge** (noted as formerly Sparebanken Vest + Sparebanken Sor). Nordnet and Bulder not explicitly confirmed in docs but may be available (Bulder is part of Sparebanken Norge). |
| **Business entity** | **Not required for personal non-commercial use.** KYB (Know Your Business) only required for production apps serving the public. |
| **TPP status** | Enable Banking is a registered AISP regulated by Finnish Financial Supervisory Authority (FIN-FSA). They act as TPP on your behalf. Licensed TPPs can also use the API under their own license. |
| **Sign-up process** | 1. Create account 2. Create production application 3. Activate by linking your own bank accounts 4. App enters "restricted mode" -- can only access your linked accounts |
| **Rate limits** | Not publicly documented for restricted mode. Bank-side PSD2 limits apply (typically 4 calls/day). |
| **API quality** | REST API with good documentation. Used by Firefly III data importer as GoCardless replacement. Some overhead: you must handle bank authentication flow and store session data yourself (sessions last up to 180 days). |
| **Limitations** | Restricted apps cannot be made public. Only your own accounts. Must re-authorize when sessions expire. |
| **Verdict** | **Best free option for new users.** Confirmed Norwegian bank coverage. No business entity needed. Some implementation overhead compared to GoCardless. |

Sources:
- [Enable Banking](https://enablebanking.com)
- [Enable Banking Core](https://enablebanking.com/core/)
- [Enable Banking Docs - Markets](https://enablebanking.com/docs/markets/)
- [Enable Banking Docs - FAQ](https://enablebanking.com/docs/faq/)
- [Enable Banking Docs - Linked Accounts](https://enablebanking.com/docs/api/linked-accounts/)
- [Firefly III Issue #10753](https://github.com/firefly-iii/firefly-iii/issues/10753)

---

## 3. Tink (owned by Visa)

| Aspect | Details |
|--------|---------|
| **Pricing** | Standard plan: ~EUR 0.50/user/month for transactions. EUR 0.25/verification for Account Check. Enterprise: custom pricing. **No free production tier.** |
| **Free tier** | Sandbox only (test data). Free account at console.tink.com for testing. |
| **Norwegian banks** | **Confirmed support for Bulder Bank, SpareBank 1 (multiple regional banks), and Nordnet.** Tink has a dedicated Norway status page (tinknorway.statuspage.io). 3,400+ banks across 18 European markets. |
| **Business entity** | Likely required for production. KYC/due diligence performed under AML/CTF framework. Sandbox is open to anyone. |
| **TPP status** | Tink acts as licensed TPP on your behalf. |
| **Sign-up** | Self-service at console.tink.com. Can test with sandbox immediately. Production requires upgrade and likely business verification. |
| **API quality** | Excellent documentation (docs.tink.com). Well-established platform. Market capabilities docs show per-country details. |
| **Verdict** | **Best commercial option with widest Norwegian bank coverage** (all 3 target banks confirmed). But no free tier for production use. |

Sources:
- [Tink Pricing](https://tink.com/pricing/)
- [Tink Docs](https://docs.tink.com/market-capabilities)
- [Tink Norway Status](https://tinknorway.statuspage.io/)
- [Tink Console](https://console.tink.com/)
- [Fintable SpareBank 1 via Tink](https://fintable.io/coverage/banks/Norway/9430_sparebank-1-smn)

---

## 4. Neonomics (Norwegian, Bergen-based)

| Aspect | Details |
|--------|---------|
| **Pricing** | Usage-based / per-transaction. **No public pricing page.** Custom quotes after sales demo. |
| **Free tier** | Sandbox for testing. No free production tier indicated. |
| **Norwegian banks** | **Strong Norwegian coverage: DNB, Sparebanken Vest/Norge, Bulder, SpareBank 1, Eika banks, DSS banks.** 420+ banks in Norway. 3,500+ banks across Europe. |
| **Business entity** | Likely required. Enterprise-oriented, sales-driven onboarding. |
| **TPP status** | Neonomics acts as licensed TPP. |
| **Sign-up** | Create account at developer portal (portal.sandbox.neonomics.io). Get Client ID and Secret. Sandbox access appears self-service. Production requires commercial agreement. |
| **API quality** | Good documentation (docs.neonomics.io). Norwegian company so strong local bank knowledge. |
| **Nordnet support** | Not confirmed in search results. |
| **Verdict** | **Best Norwegian bank coverage** given local expertise, but enterprise-oriented with no free production tier. Not suitable for individual hobby use. |

Sources:
- [Neonomics](https://www.neonomics.io)
- [Neonomics Developer Portal](https://docs.neonomics.io/docs/developer-portal)
- [Neonomics Sandbox](https://portal.sandbox.neonomics.io/)
- [Neonomics on Open Banking Tracker](https://www.openbankingtracker.com/api-aggregators/neonomics)

---

## 5. Aiia (owned by Mastercard, formerly Danish)

| Aspect | Details |
|--------|---------|
| **Pricing** | Not publicly listed. Contact sales. Now branded as "Mastercard Open Finance Solutions." |
| **Free tier** | Sandbox with demo/test banks available via Mastercard Developer Portal. No confirmed free production tier. |
| **Products** | Two tiers: **Aiia Data** (unlicensed -- for non-TPPs) and **Aiia Enterprise** (for licensed TPPs). |
| **Norwegian banks** | Connected to ~3,000 European banks. Nordea Norway confirmed. Specific Norwegian bank list not public. Originally Danish, so strong Nordic presence. |
| **Business entity** | Likely required. Mastercard Developer Portal registration needed. |
| **TPP status** | Acts as TPP for "Aiia Data" users. Licensed TPPs use "Aiia Enterprise." Legal entity: Mastercard OB Services Europe A/S. |
| **Sign-up** | Register at developer.mastercard.com. Sandbox access appears self-service. |
| **API quality** | Postman collections available on GitHub. Documentation on Mastercard developer portal (often requires JS rendering, hard to scrape). |
| **Verdict** | **Enterprise-oriented.** Potentially good Nordic coverage but pricing opacity and corporate onboarding make it unsuitable for individual/hobby use. |

Sources:
- [Mastercard Aiia Developers](https://developer.mastercard.com/product/aiia)
- [Aiia Data Docs](https://developer.mastercard.com/open-finance-europe/documentation/unlicensed/aiia-data/)
- [Mastercard Open Banking EU Postman](https://github.com/Mastercard/open-banking-eu-postman-collections)

---

## 6. Yapily

| Aspect | Details |
|--------|---------|
| **Pricing** | Custom/contact sales. "Tailored pricing for every business." No public price list. |
| **Free tier** | Sandbox only. Preconfigured sandbox environment available without signing up with banks. |
| **Norwegian banks** | **Norway is a supported country** (19 countries total). Specific Norwegian bank list not publicly detailed. |
| **Business entity** | Likely required for production. Sandbox open to developers. |
| **TPP status** | Acts as licensed TPP. |
| **Sign-up** | Developer docs at docs.yapily.com. Sandbox can be used immediately. Production requires commercial agreement. |
| **API quality** | Good documentation. Developer Slack community with engineering team access. |
| **Verdict** | Norway covered but **enterprise-oriented with no free production tier.** Not suitable for individual use. |

Sources:
- [Yapily Pricing](https://www.yapily.com/pricing)
- [Yapily Coverage](https://www.yapily.com/product/open-banking-country-coverage)
- [Yapily Sandbox Docs](https://docs.yapily.com/pages/resources/sandbox/sandbox-overview/)

---

## 7. Plaid

| Aspect | Details |
|--------|---------|
| **Pricing** | Free tier for development/testing (US-focused). Production pricing per API call, varies by product. |
| **Norwegian banks** | **Norway was listed as "coming soon" (since 2022).** Not confirmed as live. Plaid's European coverage is growing (2,000 institutions) but focused on UK, Germany, France, Spain, Netherlands, Ireland. |
| **Business entity** | Required for production use. |
| **TPP status** | Acts as TPP in supported European markets. |
| **Verdict** | **Norway likely not supported yet.** Plaid's strength is US/UK. Not a viable option for Norwegian banks currently. |

Sources:
- [Plaid European Coverage](https://plaid.com/docs/institutions/europe/)
- [Plaid Global](https://plaid.com/global/)
- [Plaid Europe Blog](https://plaid.com/blog/plaid-europe-new-partnerships-and-country-coverage/)

---

## 8. TrueLayer

| Aspect | Details |
|--------|---------|
| **Pricing** | Not publicly disclosed. Custom pricing. Claims up to 50% lower than card payments. |
| **Free tier** | Trial/introductory plans available on request. |
| **Norwegian banks** | **Limited.** TrueLayer expanded Nordic payment coverage via Lunar partnership (Denmark, Sweden, Norway) but primarily focused on UK, Ireland, and Western Europe. Only 68+ institutions total (much smaller than competitors). |
| **Business entity** | Required. Enterprise-oriented. |
| **TPP status** | Acts as licensed TPP. |
| **Verdict** | **Minimal Norwegian coverage.** Small bank network. Enterprise pricing. Not suitable for this use case. |

Sources:
- [TrueLayer](https://truelayer.com/)
- [TrueLayer on Open Banking Tracker](https://www.openbankingtracker.com/api-aggregators/truelayer)
- [TrueLayer Supported Providers](https://docs.truelayer.com/docs/supported-providers-table)

---

## Comparison Matrix

| Aggregator | Free Production | Norway | Bulder/SpNorge | SpareBank 1 | Nordnet | No Business Entity | Self-Service |
|------------|----------------|--------|----------------|-------------|---------|-------------------|-------------|
| **Enable Banking** | Yes (restricted) | Yes | Likely (SpNorge confirmed) | Yes | Unknown | Yes (personal) | Yes |
| **GoCardless** | Was free | Yes | Likely | Likely | Unknown | Was yes | **Closed to new users** |
| **Tink** | No | Yes | Yes (Bulder) | Yes | Yes | Unclear | Sandbox yes |
| **Neonomics** | No | Yes | Yes | Yes | Unknown | No | Sandbox yes |
| **Aiia/Mastercard** | No | Likely | Unknown | Unknown | Unknown | No | Sandbox yes |
| **Yapily** | No | Yes | Unknown | Unknown | Unknown | No | Sandbox yes |
| **Plaid** | No | Not yet | No | No | No | No | N/A |
| **TrueLayer** | No | Limited | Unknown | Unknown | Unknown | No | No |

---

## Key Takeaways

1. **Enable Banking is the clear winner** for your use case: free personal use, Norway supported, no business entity required, SpareBank 1 and Sparebanken Norge confirmed. The main trade-off is more implementation work (you handle auth flows yourself) and limited to your own linked accounts.

2. **GoCardless was perfect but is closed** to new signups. If you can somehow get an existing account (e.g., someone transfers one, or signups reopen), it remains the easiest free option.

3. **Tink is the best paid option** with the widest confirmed Norwegian coverage (all 3 of your target banks). The EUR 0.50/user/month is modest but requires a business relationship.

4. **Neonomics has the deepest Norwegian knowledge** (Bergen-based, 420+ Norwegian banks) but is enterprise-only.

5. **Nordnet is the hardest bank to access** via aggregators. Tink is the only one with confirmed Nordnet support. For Nordnet investment data, you may need to look at Nordnet's own (non-PSD2) APIs or screen scraping as alternatives.

6. **All aggregators act as TPP** on your behalf -- you do not need your own PSD2/AISP license.

7. **PSD2 bank-side rate limits** apply universally: typically 4 API calls per day per account, regardless of which aggregator you use. This is a bank-imposed limitation, not an aggregator limitation.
