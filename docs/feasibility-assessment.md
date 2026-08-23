# Feasibility Assessment — Banana English

Researched 2026-08-23. Verdict: **technically feasible, economically feasible only with metering,
and market-constrained in a way that changes the business model — not the product.**

The three findings that should change decisions are in bold. Everything else is supporting detail.

---

## 1. Verdict summary

| Dimension | Verdict | Why |
|---|---|---|
| Technical | ✅ Feasible | Every component is a priced, documented API. No research risk. |
| Unit economics | ⚠️ Conditional | Naive implementation is **gross-margin negative**. Metered, it's 74–85%. |
| Market size | ⚠️ Constrained | AU-Thai alone supports a side project. The full diaspora supports a real business. |
| Competition | ⚠️ Real, and free | Government-funded free classes + a $11.99 incumbent already serving Thai users. |
| Moat | ✅ Narrow but genuine | Nobody drills Thai-L1 phonemes inside Australian bureaucratic situations. |

---

## 2. Unit economics (verified rates)

**Azure Pronunciation Assessment: $1.32 per audio-hour** = $0.000367/second, billed per second, prorated.
An 8-second utterance costs ~$0.0029. First 5 audio-hours/month are free (F0 tier).
Neural TTS ~$16/1M characters, 0.5M free/month. Commitment tiers (2,000 / 10,000 / 50,000 hours) discount
at volume — irrelevant until thousands of daily users.

**Cost per user per month, by design choice:**

| Speech design | Audio scored | Cost/user/mo |
|---|---|---|
| Selective — score only shadow-focus lines (20 × 4s/day) | 80s/day | **$0.88** |
| Moderate — 3 min/day scored | 3 min/day | $1.98 |
| Naive — score everything the user says, 10 min/day | 10 min/day | **$6.61** |

| Roleplay model | Per session | 1/day | 2/day |
|---|---|---|---|
| Claude Opus 5 ($5/$25 per MTok) | ~$0.10 | $3.00 | $6.00 |
| Claude Sonnet 5 ($3/$15) | ~$0.06 | $1.80 | $3.60 |
| Claude Haiku 4.5 ($1/$5) | ~$0.02 | $0.60 | $1.20 |

**Revenue net of distribution, at ELSA's $11.99 price point:**

| Channel | Net per subscriber |
|---|---|
| App Store / Play, standard 30% | $8.39 |
| App Store / Play, Small Business Program 15% (under $1M/yr — you qualify) | $10.19 |
| **Web + Stripe (~2.9% + $0.30)** | **$11.29** |

**Margin, three ways of building the same product:**

| Build | COGS/user/mo | Margin on $10.19 net |
|---|---|---|
| Naive: score everything + Opus 5 roleplay 2×/day | $12.61 | **−24% — loses money on every subscriber** |
| Mid: selective scoring + Sonnet 5, 1 session/day | $2.68 | 74% |
| Lean: selective scoring + Haiku 4.5, 1 session/day | $1.48 | 85% |

> **Finding 1: the difference between a 85%-margin business and a loss-making one is entirely
> implementation choices — what you send to the scorer, which model answers a roleplay turn, and
> whether turns are capped.** None of it is recoverable later: you cannot take unlimited scoring away
> from users who already have it. Meter from launch.

Web-first billing avoids the 15–30% platform cut entirely — worth ~$1.10–$2.90 per subscriber per
month, which is comparable to the entire COGS. Another argument for shipping web before native.

---

## 3. Market size (the constraint)

**Australia — Thailand-born, 2021 Census: 83,779 people.**

| Attribute | Value | Implication |
|---|---|---|
| Speak English "not well or not at all" | 16.7% (~14,000) | The acute-need core |
| Speak English "well/very well" | 61.8% (~51,800) | Fluency/confidence market, softer need |
| Female | **70.1%** | Product, tone, and marketing should be built for this, not gender-neutral by default |
| Aged 25–44 | 52.4% | Working age, phone-first |
| Median personal income | **$657/week** vs $805 national | Price-sensitive. $11.99/mo is ~0.4% of weekly income — not trivial |
| Not Australian citizens | 45.7% | Visa-holders navigating exactly the Layer C scenarios |
| Arrived 2016–2021 | 24.3% | Steady replenishment of high-need new arrivals |

**The wider diaspora in English-speaking countries** (~1.1M Thai overseas worldwide):

| Country | Thai population | Note |
|---|---|---|
| United States | ~340,000 (2023) | Largest, but more established/second-generation — many are English-native |
| Australia | 83,779 (2021) | Launch market |
| United Kingdom | ~50,000–55,000 | Locale pack #2 candidate |
| NZ / Canada / Ireland | ~30,000 combined | Long tail |
| **Reachable total** | **~500,000** | The genuine ceiling, per the "English-speaking countries only" scope rule |

**Funnel math** (EdTech freemium converts at ~2.6% median; hard paywalls convert 5× better than
freemium — 10.7% vs 2.1% — per RevenueCat's 2026 subscription report):

| Scenario | Installs | Conversion | Subscribers | Net revenue/yr |
|---|---|---|---|---|
| AU only, freemium, realistic reach | 10,000 | 2.6% | 260 | ~$32k |
| AU only, **hard paywall / trial** | 10,000 | 10.7% | 1,070 | ~$131k |
| AU + UK + US, hard paywall | 50,000 | 10.7% | 5,350 | ~$654k |
| Full diaspora, mature, hard paywall | 100,000 | 10.7% | 10,700 | ~$1.3M |

> **Finding 2: freemium does not work at this market size.** Duolingo's free tier is subsidised by
> 140.6M monthly actives converting at ~9% into 12.7M subscribers — scale you will never have, on
> content that costs them nothing to serve. Your free users cost you real money per minute *and*
> there aren't enough of them for a 2.6% conversion to matter. **A short free trial behind a hard
> paywall is both the higher-converting model and the one your cost structure demands.** These point
> the same direction, which is rare — take it.

The AU-only launch is a beachhead that proves the model, not the business. The business is the
locale-pack rollout, and the plan should stop treating UK/US as optional nice-to-haves.

---

## 4. Competition

**AMEP — the Adult Migrant English Program.** Free English tuition for all permanent visa holders,
some temporary visa holders, **and citizens who previously held an eligible permanent visa** (new in the
2021 reform). The 510-hour cap was **removed in 2021 — it is now unlimited hours**, across ~300
locations, with **free childcare** for pre-school children.

**Do not assume this is only for recent arrivals — the 2021 reform inverted that.** For anyone with a
**visa commencement date on or before 1 October 2020, the time limits for enrolling, starting and
completing were removed entirely**. Those with a commencement date *after* 1 October 2020 are the ones
still subject to registration/commencement/completion limits. Combined with the citizenship pathway,
this means **long-settled Thai migrants have the least restricted access**, and given that 53.7% of
Thailand-born Australians are citizens and the largest arrival cohort (29.5%) came in 2001–2010, most of
the addressable market likely qualifies. The pre-2021 rules — 510 hours, register within 6 months,
finish within 5 years — no longer apply and should not be used to size this threat.

> **Finding 3: your target user can already get unlimited English classes, free, with childcare,
> from the Australian government.** This is the single biggest threat in the assessment and it is
> not mentioned anywhere in the existing docs.

What survives the objection — and Step 3 must test it, not assume it. Note that none of these are
"we give you access to English lessons"; that fight is lost to a free, well-funded incumbent:
- **Scheduling.** AMEP is classroom-based at fixed times and requires travel. The target user is 70%
  female, low-income, frequently in hospitality/food service/care with irregular shifts.
- **Specificity.** AMEP teaches general English. It does not rehearse "is it bulk billed?" thirty times
  until the sentence is automatic under stress.
- **Pronunciation scoring.** AMEP has none, and no Thai-L1 phoneme diagnosis. Step 0 proved we can.
- **Failing privately — the strongest one.** Fear of losing face is the documented barrier for this
  audience (see `brand-guide.md`), and a classroom of strangers is exactly where it bites hardest. A
  phone at 11pm is the one place a learner can be bad at English with no witnesses. AMEP cannot offer
  this by construction.
- Genuinely ineligible cohorts still exist: some temporary visa holders and students.

**ELSA Speak — $11.99/month, 25M+ users, and it already supports Thai as an interface language.**
Phoneme-level pronunciation feedback is its core feature. It sets your price ceiling and it is
already in your niche's general direction. It does not do situational scenarios and it does not do
Australian systems.

**Duolingo — the AI-conversation differentiator is eroding fast.** In Q2 2026 they reported 140.6M MAU
and 12.7M subscribers, and stated they have driven **Video Call cost to under 1 cent per call**, are
moving it from the premium Max tier down into Super, and are considering sunsetting Max entirely.
AI speaking practice is becoming a bundled commodity feature at a lower price point. Do not build the
pitch on "practise speaking with AI" — that will be table stakes within a year.

**What is actually defensible:** Thai-L1 phoneme targeting *inside* Australian bureaucratic situations.
ELSA has the phonemes without the situations; Duolingo has the conversation without either. Nobody
has a reason to build "Medicare bulk-billing dialogue that drills Thai final-consonant deletion" —
the market is too small for them and exactly right for you. That is the whole thesis, and the
research supports it. It is narrow, and it is real.

---

## 5. Technical feasibility

No component requires research. Everything is a documented, priced API.

| Component | Status | Risk |
|---|---|---|
| Pronunciation assessment | Azure, $1.32/hr, streaming JS samples exist | Score quality on Thai-accented English — Step 0's card/car test |
| STT with word timing | Included in the same Azure response | None |
| TTS (AU voice) | Azure Neural, pre-rendered once, ~$5 for the whole catalogue | None |
| Roleplay | Anthropic API, three price tiers | Cost, not capability |
| Content generation | ~$0.09/unit, <$100 for everything | None |
| Backend | Flask + Postgres on DigitalOcean, founder's proven stack | None |

**One correction to the web-first plan:** the Azure Speech JS SDK does support browser microphone
input and streaming pronunciation assessment, but there are **documented iOS Safari issues** — mic
permission prompt timing differs from Chrome, and cases where recognition events stop firing after
permission is granted. Web-first is still the right call; it is not the friction-free path I described.
**Validate the Azure JS SDK on a real iPhone in Safari on day one of Step 2**, before building
anything on top of it. If it fails, the fallback is `MediaRecorder` + server-side upload, which
reinstates the audio-format work but is well-trodden.

---

## 5b. Cost minimisation — ranked by saving per unit of effort

Baseline is the "lean" build from §2: **$1.48/user/month**. Applying the cheap levers below takes it to
**~$0.50/user/month** — a 96% gross margin on web-billed revenue. Nothing here requires new vendors or
new architecture; most of it is a config value or twenty lines of JavaScript.

### Speech scoring: $0.88 → ~$0.15/user/month

| # | Lever | Saving | Effort |
|---|---|---|---|
| 1 | **Trim silence client-side before sending.** Billing is per second of audio *sent*. A 4-second recording of a 3-word phrase contains ~1.5–2s of speech. An RMS gate in the browser cuts the rest. | **35–50%** | ~20 lines of JS |
| 2 | **Shorter reference texts.** Shadow 3–5 word chunks, not full sentences. Halves the audio — and the flagship already prescribes "short and repeatable" lines, so this is free pedagogically. | **~30%** | Content design, zero code |
| 3 | **Adaptive sampling.** Score every rep while a sound's accuracy is still moving; taper to 1-in-5 spot checks once it converges. Learners drill the same phonemes constantly and most reps after week one just confirm what the meter already knows. | **50–70% of what remains** | One query + a rule, using the `attempts` table you're already building |
| 4 | Azure free tier: **5 audio-hours/month**, free. | Covers the entire alpha | Zero |

**The 7× option, if speech cost ever actually hurts:** Azure real-time is $1.00/hr **+ $0.30/hr** for the
pronunciation add-on; **batch transcription is $0.18/hr and includes add-on features at no extra charge**.
Batch is job-based (minutes of latency), so it can't drive live shadowing feedback — but a hybrid can:
gate the rep instantly in-browser ("did they say the right words at all"), then send the audio to batch
for the real phoneme scoring that populates the sound meters by next session. Users get instant
in-the-moment feedback; the expensive scoring goes async at ⅐ the price.
⚠️ **Verify first** — the docs are explicit that pronunciation assessment is *not* supported on *fast*
transcription; whether it is supported on *batch* transcription is the question, and it's worth an hour
of someone's time because it is the largest single lever available.

**Don't self-host.** `kaldi-gop`, GoParrot, and Whisper-CTC GOP variants all exist and work, but a
GPU box at ~$200/month only breaks even against ~150 audio-hours — which, once the levers above are
applied, is somewhere north of 1,000 paying users. Revisit at 2,000+; not before.

### Roleplay: up to $3.00 → ~$0.30–0.50/user/month

| # | Lever | Saving | Effort |
|---|---|---|---|
| 1 | **Send the persona, curveballs, and rubric — not the whole unit JSON.** The roleplay system prompt needs ~600 tokens, not ~3,000. Vocabulary lists and culture notes do nothing for it. | **~5× on input** | Trivial |
| 2 | **`max_tokens` ≈ 150.** Output is 5× the input price and a roleplay reply is one or two sentences. This is the highest-leverage single config value in the app. | Caps the expensive half | One parameter |
| 3 | **No extended thinking on dialogue turns.** Staying in character is not a reasoning task; thinking tokens bill as output. | Large | One parameter |
| 4 | **Split the model by task.** Haiku 4.5 ($1/$5) speaks the dialogue turns; a better model scores the rubric **once at session end**, not per turn. Cheap where it's volume, good where it's judgment. | **~5× on turns** | Two call sites |
| 5 | Turn cap (12), enforced server-side. | Bounds the worst case | One constant |

⚠️ **Prompt caching does not apply here, and the two optimisations conflict.** Measured on a real
session: `cache_read: 0` every turn. The trimmed system prompt is **424 tokens** and the minimum
cacheable prefix is ~1024, so a `cache_control` marker on it is silently inert. Trimming the prompt
(lever 1) is worth more than caching would have been, but do not count both.

### Distribution — the biggest line item of all

| # | Lever | Saving |
|---|---|---|
| 1 | **Sell on the web via Stripe**, not through the app stores. | **$1.10–2.90 per subscriber per month** — more than the entire COGS |
| 2 | **Annual billing (~$99/yr).** One Stripe fee ($3.17) instead of twelve ($7.80), cash up front, and better retention than monthly. | **~$4.60/user/year** |

### Infrastructure — keep it boring

- One $12 droplet running Flask **and** Postgres. Managed Postgres ($15/mo) only once there are paying
  users whose data you can't afford to lose.
- Cloudflare free tier in front for static audio — $0 egress. Skip DO Spaces; the entire pre-rendered
  mp3 catalogue is ~100 MB and fits on the droplet.
- TTS: Azure's **0.5M characters/month free** effectively covers the whole catalogue, which is rendered
  once anyway.
- Content generation: Batch API (50% off) + a cached spec/flagship prefix → **under $50 for everything**.

### The result

| Stage | COGS/user/mo | Margin on $11.29 (web) |
|---|---|---|
| Naive build | $12.61 | negative |
| Lean build (§2) | $1.48 | 87% |
| **Lean + these levers** | **~$0.50** | **96%** |

Alpha runs at roughly **$12/month total** — one droplet — because Azure's and Anthropic's free and
low-volume tiers absorb the rest.

**What not to bother optimising:** content generation (<$50 ever), TTS (free tier covers it), and
hosting below ~1,000 users. Time spent there is time not spent on the two questions that actually
decide the outcome (§1).

---

## 6. What this changes in the plan

1. **Meter from launch.** Free tier = the four zero-marginal-cost stages (vocab, chunk drills,
   listening, culture note). Scored speaking and roleplay are paid, capped, and never unlimited.
2. **Hard paywall with a short free trial, not freemium.** 5× the conversion, and it matches the
   cost structure. Test the price in Step 3's fake paywall at $11.99 to match ELSA.
3. **Sell on the web, not (only) the app store.** Saves 15–30% — comparable to total COGS.
4. **Add "why not just do AMEP?" to the Step 3 interview script.** If users can't answer it, the
   positioning is wrong and no amount of engineering fixes that.
5. **Treat UK/US locale packs as the business, not as optional.** AU alone caps out around $130k/yr.
6. **Test the Azure JS SDK on iPhone Safari before building Step 2 on it.**
7. **Design for the actual user: 70% female, median $657/week, working irregular shifts.** Price
   sensitivity and micro-session length are product constraints, not marketing details.

---

## Sources

- [ABS 2021 Census — People in Australia born in Thailand](https://www.abs.gov.au/census/find-census-data/quickstats/2021/5104_AUS)
- [Azure Speech pricing](https://azure.microsoft.com/en-us/pricing/details/speech/) · [Pronunciation assessment billing Q&A](https://learn.microsoft.com/en-us/answers/questions/5608069/pricing-and-usage-of-pronunciation-assessment-feat)
- [Duolingo Q2 2026 shareholder letter](https://investors.duolingo.com/static-files/3c8277ee-bc94-4f5d-9b77-0db3e46f88b8) · [Q2 2026 results coverage](https://www.stocktitan.net/sec-filings/DUOL/8-k-duolingo-inc-reports-material-event-96560f3ef7ef.html)
- [AMEP overview — Dept of Home Affairs](https://immi.homeaffairs.gov.au/settling-in-australia/amep/overview) · [About the program](https://immi.homeaffairs.gov.au/settling-in-australia/amep/about-the-program)
- [ELSA Speak pricing](https://elsaspeak.com/en/elsa-subscription)
- [RevenueCat State of Subscription Apps 2026](https://www.revenuecat.com/state-of-subscription-apps) · [Education app subscription benchmarks](https://adapty.io/blog/education-app-subscription-benchmarks/)
- [Pew Research — Thai population in the U.S.](https://www.pewresearch.org/social-trends/fact-sheet/asian-americans-thai-in-the-u-s/) · [Thais in the United Kingdom](https://en.wikipedia.org/wiki/Thais_in_the_United_Kingdom)
- [Azure Speech SDK JS browser samples](https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/samples/js/browser/index.html) · [iOS Safari mic issue thread](https://github.com/Azure-Samples/SpeechToText-WebSockets-Javascript/issues/96)
