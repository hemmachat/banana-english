# CLAUDE.md — Papaya

Context file for Claude Code. Read this in full before starting any work on this repo. It summarizes product, strategy, architecture, and decisions made so far. Detailed specs live in `docs/` — this file tells you what exists and where, not the full content of each doc.

---

## 1. What this is

**Papaya** is a mobile app (iOS + Android) that teaches **Thai people to speak English**, with a speaking-first, situational-scenario curriculum — think Duolingo's habit mechanics combined with ELSA Speak's pronunciation scoring, but built specifically around how Thai speakers mispronounce English and around real-life situations, not abstract grammar.

**Market reality (researched 2026-08-23 — full detail and sources in `docs/feasibility-assessment.md`):**
83,779 Thailand-born people live in Australia; 16.7% (~14,000) speak English "not well or not at all".
The user is **70.1% female**, median personal income **$657/week** (vs $805 national), 52% aged 25–44,
45.7% non-citizens. AU alone caps out around **$130k/yr** — it is the beachhead that proves the model,
not the business. The business is the diaspora across English-speaking countries (~500k: US ~340k,
UK ~55k, AU ~84k), which is why the locale-pack architecture is load-bearing, not a nice-to-have.

**First launch market: the Thai diaspora in Australia.** Not Thailand-domestic. Reasoning: diaspora users have acute daily need (talking to a GP, a landlord, Centrelink — not aspirational self-improvement), pay Western subscription prices, and the content is defensible precisely because it's too specific for Duolingo/ELSA/Speak to economically build. The founder (Hemma) lives in Australia, which gives real authority and distribution for the first market. UK, US, and other English-speaking countries follow via the locale-pack system (Section 4) — never non-English-speaking countries, since the product's premise (practise English) collapses if English isn't the host language.

**The competitor to beat is free.** The **AMEP** (Adult Migrant English Program) gives eligible migrants
**unlimited free English tuition** — the 510-hour cap was removed in 2021 — at ~300 locations, with free
childcare. **It is not limited to recent arrivals:** anyone whose visa commenced on or before 1 October
2020 has had all enrolment/completion time limits removed, citizens who previously held an eligible
permanent visa now qualify, and it is *post*-October-2020 arrivals who still face time limits. Most of the
AU Thai market likely qualifies.

Any pitch, landing page, or user interview must answer "why not just do AMEP?" — and the answer can never
be "we give you access to English lessons". It has to be: fits shift work, rehearses one specific
transaction to automaticity, scores pronunciation (AMEP does not), and **lets you fail privately** —
fear of losing face is this audience's documented barrier and a classroom is where it bites hardest.
That answer is a hypothesis until real users confirm it.

**Audience is Thai people only** — not a general ESL app. This is a deliberate niche-over-scale bet. It keeps the brand (Papaya / som tam), the Thai-L1 pronunciation targeting, and the localization math (only ~22 scenarios differ per country) all coherent. Don't generalize the product to other L1 groups without revisiting this decision explicitly with the founder.

---

## 2. Brand

Name: **Papaya**. Full naming rationale, rejected alternatives, visual identity, palette, mascot ("Paya"), and outstanding trademark work → `docs/brand/brand-guide.md`. Read it before writing any user-facing copy, app-store listing, or marketing material.

Key point not to lose: "Papaya" is the trademark asset; "English" is a generic, swappable descriptor that belongs in the subtitle, not the core name.

---

## 3. Curriculum architecture

### 3a. The pedagogical model
Situational, function-first (CEFR "can-do" model), not grammar-first. Every scenario exists to let a learner *do* a real thing. Content is organized as **scenario units**, each following a fixed 7-stage template: warm-up vocab → model dialogue (shadowed) → chunk drills → listening comprehension → guided roleplay → free AI roleplay (off-script at B1) → register/culture note. See the worked example in `docs/curriculum/flagship-unit-medical-centre.md` — **this is the quality bar every generated unit must match.**

### 3b. Thai L1 sound targeting (the core differentiator)
Every scenario is tagged with the specific Thai-speaker pronunciation errors it stresses (final consonants, `/r/–/l/`, `th`, consonant clusters, word stress, weak forms, intonation), and drills them *inside* the situation where getting it wrong has a real cost (e.g. "left/right" in directions, "th" in medical). This sound-targeting logic is **locale-independent** — it targets the learner's first language, not the host country, so it's built once and reused across every country pack.

### 3c. Three-layer content model
- **Layer A — invariant core** (~110 scenarios): universal situations (directions, shopping, food, work, phone, social). Built once, ships everywhere.
- **Layer B — locale config**: accent, spelling, currency, emergency number, transit card names, register notes. Tiny, ~1 hour per country.
- **Layer C — locale scenarios** (~22 per country): scenarios where the underlying *system* differs by country (health, welfare/gov, education, housing, banking/tax, immigration/citizenship, work culture). The real per-country authoring work.

Full reasoning and the AU/UK/US comparison table → `docs/curriculum/localization-architecture.md`.

### 3d. Content inventory (what exists today)
| File | What it is |
|---|---|
| `docs/curriculum/scenario-registry.yaml` | 121 core (Layer A) scenarios, tiered A1–B2, each with assigned Thai sound targets |
| `docs/curriculum/locale-pack-australia.yaml` | Layer B config + 25 Layer C scenarios for Australia (Medicare, Centrelink, school enrolment, rental/bond, TFN/super, citizenship, etc.) |
| `docs/curriculum/scenario-unit-generation-spec.md` | The generation pipeline: registry → prompt → JSON schema → QA gate → Postgres. Run this through Claude Code to mass-produce units. |
| `docs/curriculum/generation-spec-locale-addendum.md` | Adds `locale` + `locale_context` to the pipeline so the same prompt produces AU/UK/US content. Includes cross-country leakage checks. |
| `docs/curriculum/flagship-unit-medical-centre.md` | Generic quality-bar unit (fully authored, not generated) |
| `docs/curriculum/au-flagship-unit-gp-appointment.md` | Australian quality-bar unit — the AU port of the medical flagship (Medicare, bulk billing, referrals) |

**None of the other ~130 scenarios have been generated yet.** That's the next major workstream — see PLAN.md.

---

## 4. Business model (decided — these are cost constraints, not preferences)

Derived from verified pricing in `docs/feasibility-assessment.md`. Getting these wrong makes the
product gross-margin negative; they cannot be retrofitted onto users who already have unlimited access.

- **Meter from launch.** Free = the four zero-marginal-cost stages (warm-up vocab, chunk drills,
  listening, register/culture note). Paid = the three that cost real money per use (shadowing,
  guided roleplay, free roleplay). Never offer unlimited scored speaking.
- **Score selectively.** Only the shadow-focus lines go to the pronunciation API (~$0.88/user/month).
  Scoring everything a learner says is ~$6.61/user/month and destroys the margin on its own.
- **Cap roleplay turns** (~12/session, N sessions/day). Uncapped turns are unbounded COGS.
- **Hard paywall with a short free trial, not freemium.** Hard paywalls convert ~5× better (10.7% vs
  2.1%), and freemium at this market size yields too few conversions to fund the free users' costs.
  Duolingo's unlimited free tier works because their core loop is client-graded static content at
  140.6M MAU; ours costs money per minute. Do not copy their model.
- **Sell on the web with Stripe**, not only through the app stores — saves the 15–30% platform cut,
  which is comparable to total COGS per subscriber.
- **Price anchor: $11.99/mo** (ELSA Speak's price, and it already ships a Thai interface). Our user's
  median income is $657/week, so price sensitivity is real.

## 5. Tech stack (decided)

- **Backend**: Flask + PostgreSQL, hosted on DigitalOcean — the founder's existing, proven stack for other products.
- **Client: web first, native later.** *(Validated on a real iPhone 2026-08-23 — mic, scoring, roleplay
  and voice all work in iOS Safari over HTTPS. Two iOS rules to keep: claim the mic synchronously inside
  the tap handler — any `await` first makes iOS refuse it silently — and keep touch targets at 44px.)* A mobile-web page (plain HTML/JS served by Flask, Azure Speech
  **JS SDK** in the browser, short-lived speech tokens minted server-side) tests everything the early
  steps need without Expo, app review, or the store cut. React Native (Expo) comes only once retention
  is proven and push notifications start earning their build cost. ⚠️ The Azure JS SDK has documented
  iOS Safari quirks (mic permission timing, events stalling after grant) — validate on a real iPhone
  before building on it; fallback is `MediaRecorder` + server-side upload.
- **Speech-to-text**: no separate vendor — Azure's pronunciation assessment response already carries
  the recognised words and offsets.
- **Pronunciation assessment**: Azure — **not** because it's the best hyperscaler, but because AWS and
  Google **don't offer pronunciation assessment at all**. Transcription APIs (Transcribe, Google STT,
  Deepgram, AssemblyAI, Whisper) return words and confidence; we need phoneme-level accuracy against a
  reference text. Only Azure, Speechace, SpeechSuper, and ELSA sell that, and Azure is the only one that
  is self-serve with public pricing. Keep the call behind a single `score_utterance()` function so
  swapping to Speechace/SpeechSuper is a day's work. Azure Pronunciation Assessment API, **$1.32 per audio-hour**, billed
  per second (an 8-second utterance ≈ $0.0029), 5 audio-hours/month free. The open question is not
  cost but quality: does it report a *final-consonant error on "card"*, or just recognise "car"? The
  per-sound meters only work if it does the former — verify before building on it.
- **Conversational AI (roleplay engine)**: Claude, via the Anthropic API. Model tier is a live cost
  decision — Opus 5 ($5/$25 per MTok) ≈ $0.10/session, Sonnet 5 ≈ $0.06, Haiku 4.5 ≈ $0.02. Cache the
  unit JSON in the system prompt (cache reads ~0.1×). Test quality on real transcripts before choosing;
  do not downgrade on price alone. **Note the competitive trend**: Duolingo has driven AI video-call
  cost under 1 cent per call and is moving it into a cheaper tier — "practise speaking with AI" is
  becoming table stakes, so the pitch must rest on Thai-L1 targeting + AU situations, not on the
  existence of an AI roleplay partner. System prompt enforces the scenario's curriculum: correct errors, stay in-scenario, explain in Thai, follow the `roleplay_rubric` from the generated unit JSON. **Reuse the founder's existing MockPatient architecture** (persona + flexible-but-scripted encounter + rubric scoring) — same shape as the free-roleplay stage needs; don't rebuild this from scratch.
- **TTS**: multiple accent voices needed — Australian English is the priority voice for launch (not the
  American default most apps ship). **Speak at `+18%` rate** (`SPEECH_RATE`, applied via SSML prosody in
  both `render_audio.py` and the browser) — a tester found the default unrealistically slow, and
  shadowing a slowed-down model trains a target that doesn't exist in a real GP's waiting room.
  **Pre-render dialogue lines and vocabulary at content-build time**
  (`backend/render_audio.py`); never synthesize fixed content per request. The whole AU flagship's audio
  cost **$0.01** — 28 clips, 615 chars, against a 500k chars/month free tier. TTS is not a cost problem.
- **Do not use the browser's `speechSynthesis` for model audio.** It's free, but it plays whatever voice
  the device happens to have (often US, sometimes none), which destroys both the Australian-accent
  premise and the ceiling calibration — the scores are computed against specific en-AU neural voices, so
  the learner must be shadowing those same voices. You would trade the differentiator to save a cent.
  Browser *recognition* is a different question: it may later serve as a free instant gate in front of
  Azure's cheaper batch endpoint (see feasibility §5b), but that's an optimisation, not a default.
- **Content generation**: the scenario-unit generation pipeline (Section 3d) runs through Claude Code / the Anthropic API, not hand-authored per unit.

## 6. Data model notes

- Content tables need a `locale` dimension: `locale = 'global'` for core content, `locale = 'en-AU'` (etc.) for locale packs. Resolution at runtime = `global ∪ locale pack for user's locale`, pack wins on shared `scenario_id`.
- **Error-tracking is the product's brain.** Log every pronunciation/comprehension attempt against its target phoneme/skill so the app can adaptively resurface a learner's specific weak sounds. Design this table carefully — it's the retention engine (per-sound accuracy meters, adaptive drilling).
- Gamification state: streaks measured in **minutes spoken**, not lessons completed; XP per completed sub-step within a scenario, not just per unit. Store the user's **timezone** — streak day-boundaries break the first time someone flies to Thailand, which this user base does constantly.
- Derive streaks, XP, and per-sound meters from the attempts log with `GROUP BY`; don't build separate progress/streak/xp tables.

## 6b. Design principle learned from testing: separate input speed from output speed

A tester rushed to keep up with the fast GP voice and **mispronounced "bulk billed"** — the single
hardest and most consequential phrase in the AU flagship. Both halves of that are true at once:

- **Input must be fast.** Real Australians speak quickly. A slowed-down model trains comprehension
  for a conversation that doesn't exist. Model audio stays at `+18%`.
- **Output must never be hurried.** In a real GP visit nobody makes you answer fast — the pressure
  is imagined, and it degrades pronunciation exactly where accuracy matters most.

**So the product must actively give the time back**, in every stage and every future unit:
- The AI persona never fills silence, never rushes, and when a word comes out garbled it asks for it
  again ("Sorry, say that again for me?") rather than guessing past it — the learner needs the second
  attempt more than the conversation needs to move on.
- Mic cutoff errs long (2.5s in roleplay, 0.8s in shadow drills where the utterance is one short line).
- The UI says so out loud: *"The doctor talks fast — you don't have to."*

Never resolve this tension by slowing the model audio down. Slow input teaches a fiction; the fix is
removing the learner's sense of a deadline.

## 7. Non-negotiables (apply to all future content generation)

1. Every generated unit must be checked against the relevant flagship (`flagship-unit-medical-centre.md` for generic, `au-flagship-unit-gp-appointment.md` for AU) — depth, structure, and Thai-targeting must match, not just the schema.
2. **Thai strings in every file so far are first-draft and unverified.** A native Thai speaker must review all `th:` fields before anything ships. Do not treat existing Thai text as final.
3. **Australian system facts (Medicare, Centrelink, TFN, bond rules, citizenship test format, etc.) are written at founder/author confidence, not verified.** These need a local fact-check (ideally someone who works in or recently navigated these systems) before shipping — wrong health/welfare information is the highest-trust-cost error this product can make.
4. Locale content must pass the cross-country leakage check (no US/UK terms in an AU unit, and vice versa) — see the QA section of the locale addendum.
5. "Papaya" trademark clearance is **not done** — see brand-guide.md. Don't treat the name as legally locked yet.
6. Don't expand the audience beyond Thai people, and don't add a new country that isn't primarily English-speaking, without an explicit decision from the founder — both were deliberate scope calls.
7. **Never ship unlimited scored speaking or uncapped roleplay**, in any tier, at any point. See Section 4 — this is an economics constraint, and it is irreversible once users have it.
8. Every piece of user-facing positioning must survive the question **"why not just do AMEP?"** (Section 1).

---

## 8. Where things stand right now

**A working vertical slice exists.** As of 2026-08-23 the repo contains a running app, not just specs:

- `backend/` — Flask + Postgres (three tables: `units` jsonb, `users`, `attempts`), speech-token
  endpoint, roleplay + rubric scoring, profile/rewards. `backend/README.md` explains the shape.
- `backend/static/index.html` — the whole client, one file, no build step.
- `content/en-AU/au_gp_appointment.json` — the AU flagship as structured content: A2 + B1 dialogues,
  calibrated ceilings, drafted Thai, per-sound `scoring_method`.
- `spike/` — the Step 0 speech spike and its findings (`spike/README.md` §6b–6e). **Read those before
  changing anything about scoring** — they overturned several assumptions in the original spec.

Still specification-only: the other ~145 scenarios, the generation pipeline (`PLAN.md` Step 4), and
every human checkpoint (Thai review, AU fact-check, trademark, real-user testing).

- `PLAN.md` — the build sequence, ordered by risk retired per day of work.
- `docs/feasibility-assessment.md` — verified costs, market sizing, competition, and the go/no-go
  conditions. Read it before making any pricing, tier, or platform decision.
