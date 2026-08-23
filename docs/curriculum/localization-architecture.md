# Localization Architecture — build once, localize the thin layer

Goal: ship **Australia first**, but structure the product so adding the UK, US, or any other country is authoring a *locale pack*, not rebuilding the app. This document defines the layers, the template every new country fills in, and the rollout order.

---

## 1. The core idea: three layers

Most of what a Thai learner needs is the same everywhere — directions, food, shopping, phone calls, small talk, work. What changes country to country is a *system*: the health system, the welfare office, the school enrolment process, the accent. So we separate:

| Layer | What it is | Ships | Authored |
|---|---|---|---|
| **A — Invariant core** | ~75% of scenarios + all pedagogy, the Thai L1 sound engine, the generation pipeline, gamification | In every locale, unchanged | Once |
| **B — Locale config** | Accent, spelling, currency, emergency number, date format, transit-card names | Per country, tiny | Once per country (minutes) |
| **C — Locale scenarios** | ~20–25 country-specific scenarios: health, welfare/gov, education, housing, banking/tax, immigration/citizenship, work culture | Per country | Once per country (the real work) |

**The whole strategy in one line:** Layer A is your product; Layers B and C are what you re-author per country. A new country ≈ one accent voice + a spelling pass + ~22 scenarios.

---

## 2. The decision rule: is a scenario core or locale-specific?

Ask: **does the language change because the underlying *system* changes?**

- "Asking for directions," "ordering coffee," "a job interview," "telling a story" → the language is the same in Sydney, London, or LA. **Core (Layer A).**
- "Talking to your GP," "a Centrelink appointment," "enrolling your kids in school," "getting a Tax File Number" → the vocabulary, the agency names, the process, even the politeness norms differ by country. **Locale-specific (Layer C).**

Edge cases resolve cleanly with this rule: "renting an apartment" is *locale-specific* (bond vs deposit-protection-scheme vs credit-check-and-first-last-month differ a lot), while "complaining that the aircon is broken" once you're in the flat is *core*.

---

## 3. What moves out of the Thailand registry

From the existing 121-scenario registry, when you localize you **drop** the Thailand-resident items (they don't apply abroad): `immigration_visa_extension`, `ninety_day_reporting`, `work_permit_office` (Thai version), and the Thailand-only transport (`motorbike_taxi_songthaew`, `bts_mrt_skytrain`) — these are replaced by host-country equivalents in Layer C. Everything else (≈110 scenarios) stays as core.

---

## 4. The locale-pack template (what every new country supplies)

### 4a. Config block (Layer B)
```yaml
locale: en-AU
model_accent: Australian English      # the TTS voice + pronunciation model target
spelling: en-AU                        # -ise/-our/-re (organise, colour, centre)
currency: AUD ($)
number_format: "1,234.56"
date_format: DD/MM/YYYY
emergency_number: "000"
transit_cards: [Opal, Myki, Go card, Metrocard]
politeness_note: "casual register is normal; first names common; 'no worries'"
```

### 4b. Scenario slots (Layer C) — the categories every country must fill
Each country authors ~22 scenarios across these fixed categories, so packs stay comparable:

1. **Health system** — GP/primary-care visit, enrolling in the health scheme, hospital/ED, pharmacy, specialist referral, dentist.
2. **Welfare / government services** — the main benefits/services agency, the online gov portal (often by phone), proof-of-identity.
3. **Education** — enrolling children in school, parent-teacher meeting, childcare/early years, adult study (vocational).
4. **Housing** — rental application & inspection, deposit/bond, dealing with the letting agent, utilities connection.
5. **Banking & tax** — opening a bank account as a newcomer, the tax-ID process, basic tax/retirement-savings.
6. **Immigration & citizenship** — visa/immigration enquiry, the citizenship test & interview, any English-test requirement.
7. **Work culture** — host-country workplace norms, the locally-flavoured job interview, casual vs formal register.
8. **Transport specifics** — the local ticketing system, transferring/getting a driver's licence.

---

## 5. How three countries differ (concrete pattern)

This is why Layer C can't be written once. Same learner need, different system:

| Need | Australia | UK | US |
|---|---|---|---|
| See a doctor | GP, **Medicare**, "bulk billing" (no out-of-pocket) | GP, **NHS**, register with a surgery | Health **insurance**, copay, in-network |
| Emergency call | **000** | **999** (or 112) | **911** |
| Welfare/benefits | **Centrelink** / Services Australia, **myGov** | **Universal Credit**, **GOV.UK** | Patchwork (SNAP, Medicaid) — no single agency |
| Tax ID | **TFN** (Tax File Number), **ATO** | **National Insurance number**, HMRC | **SSN** (Social Security Number), IRS |
| Rent a home | **Bond** (~4 wks), lodged with a bond authority | **Deposit** in a protection scheme, "lettings agent" | Credit check, first + last + security deposit |
| Retirement saving | **Superannuation** ("super") | Workplace pension | 401(k) |
| Become a citizen | Citizenship **test + interview** | **Life in the UK** test | **USCIS** naturalization / civics test |
| Transit card | Opal / Myki / Go card | Oyster / contactless | MetroCard / Clipper / regional |

The accent differs too, which matters for a *speaking* app: an Australian-market app should model **Australian English** for both the TTS voices and the pronunciation targets, not the American default most apps ship.

---

## 6. Data-model implication (for your Postgres schema)

Add a `locale` dimension to content, so one codebase serves all countries:

- Core content rows: `locale = 'global'` (or `NULL`).
- Locale-pack rows: `locale = 'en-AU'`, keyed by `scenario_id`; they **override or add** at render time.
- Resolution at runtime: `global core ∪ locale-pack for the user's locale`, with the pack winning on any shared `scenario_id`.
- The **generation prompt** gains two injected fields: `locale` and `locale_context` (the config block + a one-paragraph description of the relevant system), so the same pipeline produces AU, UK, or US content by swapping the context.
- The **Thai L1 sound engine is locale-independent** — it targets the learner's first language, not the host country — so it needs no per-country work. That's a big saving: your hardest-to-build component is built once.

---

## 7. Rollout order (and an important filter)

> **Sizing added 2026-08-23** (`docs/feasibility-assessment.md`): this rollout is not an expansion plan,
> it *is* the business plan. Australia has 83,779 Thailand-born residents and caps out around $130k/yr
> even executed well. The US (~340,000 Thai) and UK (~50–55,000) are where the ~500k reachable diaspora
> — and a $650k–1.3M business — actually lives. Sequence AU first for validation, but do not treat
> Layers B and C for UK/US as optional polish.


1. **Australia** — first, because you're embedded in the market: you understand Medicare, Centrelink, the school system, and the accent, and you can user-test with a reachable local community.
2. **UK** — second, because the systems are Commonwealth-adjacent (NHS, GP referrals, bond-like deposits), so the AU pack ports with moderate edits, plus a British-English accent voice.
3. **US** — third, because it's the *most* different (private insurance, no single welfare agency, SSN, credit-based renting) and the largest Thai diaspora — worth doing, but it's a fuller re-author.
4. **Then other English-speaking destinations** — New Zealand, Canada, Ireland, Singapore. These reuse most of the UK/US work.

**The filter that saves you wasted planning:** the product's premise is *practising English*. That only holds where **English is the host language**. Large Thai communities also exist in Germany, Sweden, South Korea, and Japan — but a Thai person in Berlin primarily needs *German*, not English, so the value proposition collapses there. So "other countries" should mean other **English-speaking** countries. Non-English destinations would require a different product (English-as-lingua-franca, or a pivot to the local language) — a separate decision, not a locale pack.

---

## 8. Effort per new locale (rough)

- Layer B config: ~1 hour.
- Layer C scenarios: ~22 runs through the existing generation pipeline + human review against the flagship bar — the bulk of the work, but bounded and repeatable.
- One accent TTS voice for the new model_accent.
- A spelling/idiom pass over core content (mostly automated: -ize→-ise, etc.).
- Native review of the host-country facts **and** the Thai strings.

Because Layer A (your product) and the sound engine don't change, each new country is content work on a stable platform — which is exactly the position you want to be in.
