## 1. Executive summary

**Verdict: not feasible as it stands. The must need N2 (mapping of product codes across the 2024 code change) is unmet, and an unmet must need makes the overall verdict not feasible.** The other must needs (N1 sales, N3 temperature) are workable with conditions.

Facts that drive the verdict:

1. **N2 is unmet.** The product list (`internal.sales.products`) holds only codes in force after 2024-04-01. The wiki (product_codes_2024, 2024-04-02) says no mapping table exists and that name matching is not unique. No source gives the pre-2024 "L" codes.
2. **Product-level history cannot be linked across the code change.** Without a crosswalk, product-level comparisons over the history window are not possible. A product-agnostic daily total for N1 is a fallback named in the discovery results. It does not need the crosswalk.
3. **Sales history has a known gap.** The wiki records no rows in `sales.daily_by_product` for 2024-02-05 to 2024-03-10. The catalog says coverage is continuous from 2022-01-01. The two records conflict. Treat the gap as missing, not zero.
4. **Temperature is available.** Open-Meteo daily `temperature_2m_max` responded at both window ends (history and recent). It is CC BY 4.0 with attribution, but the record also lists Copernicus C3S terms, and the shop's location is not yet fixed.
5. **Holidays are partly covered.** Nager.Date returned data for 2024 and 2026. 2023 and 2025 were not probed. The licence of the hosted data is not stated.

## 2. Need coverage

| need id | need | priority | status | best source(s) | gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met with conditions | internal.sales.daily_by_product | Till gap 2024-02-05 to 2024-03-10. Code break needs a crosswalk. Access restricted. Recent-window system unconfirmed. |
| N2 | Mapping of product codes before and after the 2024 code change | must | **unmet** | internal.sales.products (name reference only) | No mapping table. Products table holds current codes only. Name matching not unique. |
| N3 | Daily maximum temperature | must | met with conditions | api.open_meteo_archive | Shop coordinates unconfirmed (Milan-area probe point used). Full range not fetched. Upstream C3S terms to confirm. |
| N4 | Public holidays in Italy | should | partially met | api.nager_public_holidays | Hosted-data licence not stated. 2023 and 2025 not probed. Ferragosto and Easter Monday unconfirmed. No regional holidays. |
| N5 | Shop opening days and local events | should | partially met | internal.store.calendar | Access not tested. is_open source and event completeness undocumented. Location unknown. Row count inconsistent with coverage. |

## 3. Source assessments

Order: with conditions first, then not feasible. No source was rated feasible without conditions.

### internal.sales.daily_by_product: feasible with conditions
- **What it is:** Till-system table of units sold and revenue (EUR) per product code per day. Owner: Retail Operations. Catalog coverage 2022-01-01, open end, daily refresh (last metadata update 2026-10-14).
- **Verdict:** Core source for N1. Does not serve N2.
- **Key flags:**
  - ACC-RESTRICTED (major): access required, classification confidential, request via Retail Operations. Not probed.
  - GOV-CATALOG-WIKI-CONFLICT (major): catalog says no gaps. Wiki says no rows 2024-02-05 to 2024-03-10. Wiki also says the recent-window source system is undocumented after the till replacement.
  - INT-JOIN-KEY-MISMATCH (major): codes ending in "L" were replaced from 2024-04-01. No mapping table.
- **Conditions:** access approval recorded; treat the gap as missing; confirm the recent extract comes from the same till system; build product-level views only after an owner-validated crosswalk, or use a daily total; confirm whether units and revenue net off voids, refunds and discounts (undocumented); run value checks (negatives, zeros, closed days) once access is granted. No sample was read.

### api.open_meteo_archive: feasible with conditions
- **What it is:** Historical weather archive API queried by latitude, longitude and timezone. Relevant field: daily `temperature_2m_max` (°C). Probed at 45.448 N, 9.169 E (138 m), a Milan-area point chosen by the profiler. Probes covered 2023-06-01 to 2023-06-03, 2025-06-01 to 2025-06-05 and 2026-03-25 to 2026-03-31.
- **Verdict:** Serves N3.
- **Key flags:**
  - LIC-MIXED (major): licence is CC BY 4.0 for API data as stated by the provider, but upstream Copernicus C3S terms are also listed. The licence page does not map C3S to the archive endpoint. Commercial use is "unknown".
  - LIC-ATTRIBUTION (minor): the attribution text "Weather data by Open-Meteo.com" is required.
- **Conditions:** confirm the upstream dataset and C3S commercial terms; add attribution to outputs; fetch the full range in a staged download (only the ends were probed); fix the shop's coordinates and set timezone Europe/Rome (the register default is Lisbon, to be replaced); request only daily `temperature_2m_max`; check the provisional-versus-final policy for recent days. Reanalysis may smooth extremes compared with station data (not verified).

### api.nager_public_holidays: feasible with conditions
- **What it is:** Per-year REST endpoint returning Italian public holidays as one record per holiday date. Days without a holiday are absent, not marked. Probes: 13 holidays for 2024 (last 2024-12-26), 14 for 2026 (last 2026-12-26). 2023 and 2025 not probed. Owner null. Refresh cadence unknown.
- **Verdict:** Serves N4 partially. The verdict is feasible with conditions, but see the blocker-severity flag below.
- **Key flags:**
  - LIC-UNKNOWN (severity blocker, judgement): the MIT licence cited is for the Nager.Date software repository. The licence of the hosted holiday data is not stated. nagerholidays.com was not allowlisted and was not read. Commercial use is "unknown".
  - GOV-OWNER-UNKNOWN (major, judgement): no owner or steward recorded. The only publisher is the Nager.Date project.
- **Conditions:** obtain and record the data licence, not the software licence, and confirm commercial use before production use; probe 2023 and 2025; confirm Ferragosto (15 Aug) and Easter Monday; flag Easter Sunday and other Sunday holidays so they are not double counted; join as a daily flag; regional or shop-specific holidays are not covered.

### internal.store.calendar: feasible with conditions
- **What it is:** Daily shop calendar with one row per day, a boolean `is_open` and a free-text `event_name`. Owner: Store Operations. Catalog coverage from 2022-01-01, open end, weekly refresh (last 2026-10-10). Catalog row count about 1500. No wiki page. Catalog only: no sample taken.
- **Verdict:** Serves N5 partially. Also gives closed-day context for N1.
- **Key flags:**
  - ACC-RESTRICTED (major, rule): access required, classification internal, open to analytics roles. Not tested for this project.
  - DQ-UNDOCUMENTED-SCHEMA (major, judgement): is_open source unknown. event_name has no dates, source or completeness field. No location field.
- **Conditions:** obtain access and sample `is_open` and `event_name`; confirm which city or branch it covers; resolve the row count (about 1500 rows against roughly 1750 days from 2022-01-01 to 2026-10-14); confirm how is_open is set for the 2024 till-gap days (the claim that it checks the gap is not supported by the wiki); treat event_name as incomplete until the owner confirms.

### internal.sales.products: not feasible
- **What it is:** Static reference list of current product codes, names and categories. About 64 rows. Owner: Retail Operations. Last metadata update 2025-03-31. No time dimension.
- **Verdict:** Cannot serve N2. It is a name reference only.
- **Key flags:**
  - INT-NO-JOIN-KEY (major, judgement): holds only codes in force after 2024-04-01. Wiki says no mapping table exists. Name matching is not unique.
- **Conditions:** use only as a name reference for a manual crosswalk, with owner validation of ambiguous names; N2 needs a true old-to-new mapping from Retail Operations.

## 4. Red-flag register

| source_id | code | severity | evidence | raised by (rule or judgement) |
|---|---|---|---|---|
| api.nager_public_holidays | LIC-UNKNOWN | blocker | Hosted data licence not stated. MIT cited is for the software repo. Commercial use unknown. | judgement |
| api.nager_public_holidays | GOV-OWNER-UNKNOWN | major | ownership.owner and steward null. | judgement |
| api.open_meteo_archive | LIC-MIXED | major | CC BY 4.0 for API data, C3S terms also listed. Mapping to archive endpoint not stated. | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | Attribution required. | rule |
| internal.sales.daily_by_product | ACC-RESTRICTED | major | Auth required, confidential. Not probed. | rule |
| internal.sales.daily_by_product | GOV-CATALOG-WIKI-CONFLICT | major | Catalog: continuous coverage. Wiki: no rows 2024-02-05 to 2024-03-10. | judgement |
| internal.sales.daily_by_product | INT-JOIN-KEY-MISMATCH | major | "L" codes re-keyed from 2024-04-01. No mapping table. | judgement |
| internal.sales.products | INT-NO-JOIN-KEY | major | Current codes only. No mapping. Names not unique. | judgement |
| internal.store.calendar | ACC-RESTRICTED | major | Auth required. Access not confirmed for this project. | rule |
| internal.store.calendar | DQ-UNDOCUMENTED-SCHEMA | major | is_open source unknown. event_name incomplete. No location. | judgement |

Note: the rule engine raised no warnings (rule_warnings is empty). The LIC-UNKNOWN blocker is a judgement flag. It sits on a source whose verdict is "feasible with conditions" because N4 is a should need.

## 5. Conditions and owners

| condition | source(s) | who can resolve it | blocking which need |
|---|---|---|---|
| Owner-validated old-to-new product code crosswalk, or mapping table | internal.sales.products; internal.sales.daily_by_product | Retail Operations (steward) | N2 (must); product-level N1 for history |
| Access approval via request process; record it | internal.sales.daily_by_product | Retail Operations | N1 (must) |
| Confirm till-system source for 2025-06 to 2026-03 extract | internal.sales.daily_by_product | Retail Operations | N1 recent window |
| Confirm void, refund and discount treatment of units and revenue | internal.sales.daily_by_product | Retail Operations | N1 |
| Treat 2024-02-05 to 2024-03-10 as missing; resolve catalog-wiki conflict | internal.sales.daily_by_product | Retail Operations | N1 (history) |
| Shop coordinates and timezone (Europe/Rome); record in decisions.md | api.open_meteo_archive | Analytics lead | N3 (must) |
| Upstream C3S commercial terms for archive endpoint | api.open_meteo_archive | Legal | N3 (must) |
| Staged full-range download; daily temperature_2m_max only; attribution | api.open_meteo_archive | Analytics engineer | N3 (must) |
| Hosted holiday data licence and commercial use | api.nager_public_holidays | Legal / analytics lead | N4 (should) |
| Owner for holiday data | api.nager_public_holidays | Analytics lead to assign | N4 (should) |
| Probe 2023 and 2025; check Ferragosto and Easter Monday | api.nager_public_holidays | Analytics engineer | N4 (should) |
| Calendar access; sample is_open and event_name | internal.store.calendar | Store Operations | N5 (should) |
| Calendar location (city or branch) | internal.store.calendar | Store Operations | N5 (should); N1 closed-day context |
| Row count mismatch (about 1500 vs about 1750 days) | internal.store.calendar | Store Operations | N5 (should) |
| is_open source and handling of till-gap days | internal.store.calendar | Store Operations | N5 (should); N1 gap handling |

## 6. Recommended next steps

1. **Raise the N2 request first.** Ask Retail Operations for an owner-validated old-to-new code mapping for codes ending in "L" and their replacements from 2024-04-01. This is the gate for the overall verdict.
2. **Raise the sales access request** through the Retail Operations process. Ask for confirmation of the till system used for the recent extract and of void, refund and discount treatment.
3. **Raise the calendar access request** with Store Operations. Ask for the location covered, the is_open source, event completeness and the row-count check.
4. **Raise the licence requests.** Ask Legal for the hosted holiday data licence (not the MIT software licence). Ask Legal for the C3S commercial terms behind the Open-Meteo archive endpoint.
5. **Decide the shop location.** Choose and justify coordinates and timezone, and record them in decisions.md. The page was not found. The Milan-area probe point is only a placeholder.
6. **Decide the fallback for N1.** Decide whether a product-agnostic daily total is acceptable if the crosswalk is not delivered. This would let N1 and N3 proceed without product-level history.
7. **Decide whether to accept the Nager blocker-severity flag.** Decide whether N4 can proceed with the licence still open, or whether it waits for the licence.
8. **Once the gate is passed, profile in this order:** (a) sales value checks for the history window (negatives, zeros, closed days) and the 2024-02-05 to 2024-03-10 gap; (b) the calendar row count and is_open values; (c) Open-Meteo full-range coverage and the provisional-versus-final policy for recent days; (d) Nager 2023 and 2025 coverage and the Ferragosto and Easter Monday entries.

## 7. Open questions for the human reviewer

See the `open_questions_for_human` field.

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-10T17:17:01Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- api.nager_public_holidays: LIC-UNKNOWN

**Open questions:**

1. Which city or branch does the shop sit in, and which coordinates and timezone will you use for the Open-Meteo call? The decisions.md page was not found, so no assumption is recorded yet.
2. Does Retail Operations hold an old-to-new product code mapping for the 2024-04-01 change? If not, is a product-agnostic daily total acceptable as the N1 fallback?
3. Is the 2024-02-05 to 2024-03-10 sales gap a true missing period, as the wiki says, or do the catalog's continuous-coverage claim and the calendar's is_open values show otherwise?
4. Does the 2025-06 to 2026-03 sales extract come from the same till system as the history? Retail Operations has not confirmed this.
5. Do units_sold and revenue_eur net off voids, refunds and discounts?
6. What is the licence of the hosted Nager.Date holiday data, and is commercial use allowed? The MIT licence cited is for the software repository only. Who is the accountable owner?
7. Are the C3S terms listed for Open-Meteo applicable to the archive endpoint, and does commercial use of the outputs fall under them?
8. Should the holiday source (api.nager_public_holidays) keep the verdict 'feasible with conditions' while carrying a blocker-severity licence flag? Or should it be reclassified until the licence is recorded?
9. Who owns the shop calendar's is_open and event_name data, how is is_open set, and which city or branch does it cover? The row count (about 1500) does not match the expected days from 2022-01-01.
10. Is Retail Operations willing to validate ambiguous product names, given that the wiki says names are not unique?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
